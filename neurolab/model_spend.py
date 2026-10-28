"""Shared conservative model-call reservations; never an invoice or usage estimate."""

from __future__ import annotations

import hashlib
import json
import math
import os
import uuid
from dataclasses import asdict, dataclass
from decimal import ROUND_CEILING, Decimal, InvalidOperation

from .model_configuration import model_configuration


class ModelSpendError(RuntimeError):
    """Sanitized budget configuration, ownership or storage failure."""


class ModelSpendLimitError(ModelSpendError):
    """A shared reservation ceiling would be exceeded before transport."""


def _positive_decimal(name):
    value = os.getenv(name, "")
    try:
        number = Decimal(value) if len(value) <= 32 else Decimal("NaN")
    except InvalidOperation:
        number = Decimal("NaN")
    if (
        not number.is_finite()
        or not 0 < number <= 1_000_000
        or len(number.as_tuple().digits) > 18
        or number.as_tuple().exponent < -9
    ):
        raise ModelSpendError(
            "Model spending requires explicit positive bounded pricing and limits"
        )
    return number


def _micro_limit(name):
    value = _positive_decimal(name) * 1_000_000
    if value != value.to_integral_value():
        raise ModelSpendError("Model spending limits require at most six decimal places")
    return int(value)


@dataclass(frozen=True)
class SpendPolicy:
    provider: str
    model_id: str
    endpoint_sha256: str
    input_usd_per_million: str
    output_usd_per_million: str
    run_micro_usd: int
    owner_day_micro_usd: int
    global_day_micro_usd: int
    input_overhead_tokens: int
    run_tokens: int

    @classmethod
    def from_environment(cls):
        try:
            overhead = int(os.getenv("MODEL_INPUT_OVERHEAD_TOKENS", ""))
            tokens = int(os.getenv("MODEL_MAX_RUN_TOKENS", "100000"))
        except ValueError:
            raise ModelSpendError(
                "Model token overhead and run budget must be configured"
            ) from None
        if not 1 <= overhead <= 8192 or not 100 <= tokens <= 100_000:
            raise ModelSpendError("Model token overhead or run budget is outside allowed limits")
        try:
            config = model_configuration()
        except ValueError as exc:
            raise ModelSpendError(str(exc)) from None
        provider, model, endpoint = config.provider, config.model_id, config.endpoint
        if (
            not model
            or len(model) > 200
            or not endpoint.startswith("https://")
            or (provider == "baseten" and not config.configured)
        ):
            raise ModelSpendError(
                "Model spending requires an explicit approved provider and model endpoint"
            )
        return cls(
            provider,
            model,
            hashlib.sha256(endpoint.encode()).hexdigest(),
            format(_positive_decimal("MODEL_INPUT_USD_PER_MILLION_TOKENS").normalize(), "f"),
            format(_positive_decimal("MODEL_OUTPUT_USD_PER_MILLION_TOKENS").normalize(), "f"),
            _micro_limit("MODEL_MAX_COST_USD"),
            _micro_limit("MODEL_OWNER_DAILY_COST_USD"),
            _micro_limit("MODEL_GLOBAL_DAILY_COST_USD"),
            overhead,
            tokens,
        )

    @property
    def serialized(self):
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @property
    def digest(self):
        return hashlib.sha256(self.serialized.encode()).hexdigest()

    def charge(self, input_tokens, output_tokens):
        # USD per million tokens multiplied by tokens equals micro-USD.
        return int(
            (
                Decimal(input_tokens) * Decimal(self.input_usd_per_million)
                + Decimal(output_tokens) * Decimal(self.output_usd_per_million)
            ).to_integral_value(rounding=ROUND_CEILING)
        )


class ModelSpendGuard:
    def __init__(self, store, owner_id, scope_id, provider, model_id, policy):
        if (
            not owner_id
            or not scope_id.startswith(("run:", "refine:", "smoke:"))
            or len(scope_id) > 80
        ):
            raise ModelSpendError("Model spending requires a server-owned execution scope")
        self.store, self.owner_id, self.scope_id = store, owner_id, scope_id
        if provider != policy.provider or model_id != policy.model_id:
            raise ModelSpendError("Model identity differs from the approved spending policy")
        self.provider, self.model_id, self.policy = provider, model_id, policy

    def check_transport(self, endpoint, provider, model_id):
        if (
            provider != self.provider
            or model_id != self.model_id
            or hashlib.sha256(endpoint.encode()).hexdigest() != self.policy.endpoint_sha256
        ):
            raise ModelSpendError("Model endpoint differs from the approved spending policy")

    @classmethod
    def from_environment(cls, store, owner_id, scope_id, provider, model_id):
        return cls(store, owner_id, scope_id, provider, model_id, SpendPolicy.from_environment())

    def _check_owner(self):
        user = self.store.get_user(self.owner_id)
        if not user or not user["is_active"]:
            raise ModelSpendError("Model spending requires an active resource owner")
        if self.scope_id.startswith("run:") and not self.store.get_run(
            self.scope_id[4:], owner_user_id=self.owner_id
        ):
            raise ModelSpendError("Model spending scope does not belong to the resource owner")

    def _check_policy(self):
        row = self.store._execute(
            "SELECT policy_sha256 FROM model_spend_control WHERE control_id=1"
        ).fetchone()
        if row["policy_sha256"] is None:
            _write_policy(self.store, self.policy, None, "first_admission")
        elif row["policy_sha256"] != self.policy.digest:
            raise ModelSpendError(
                "Model spending policy differs from the shared policy; operator review required"
            )

    def _check_totals(self, day, charge, tokens):
        daily = self.store._execute(
            "SELECT COALESCE(SUM(reserved_micro_usd),0) AS global_day, "
            "COALESCE(SUM(CASE WHEN owner_user_id=? THEN reserved_micro_usd ELSE 0 END),0) AS owner_day "
            "FROM model_spend_reservations WHERE day_number=?",
            (self.owner_id, day),
        ).fetchone()
        scope = self.store._execute(
            "SELECT COALESCE(SUM(reserved_micro_usd),0) AS scope_cost, "
            "COALESCE(SUM(input_tokens+output_tokens),0) AS scope_tokens "
            "FROM model_spend_reservations WHERE scope_id=?",
            (self.scope_id,),
        ).fetchone()
        limits = (
            (daily["global_day"] + charge, self.policy.global_day_micro_usd),
            (daily["owner_day"] + charge, self.policy.owner_day_micro_usd),
            (scope["scope_cost"] + charge, self.policy.run_micro_usd),
            (scope["scope_tokens"] + tokens, self.policy.run_tokens),
        )
        if any(amount > limit for amount, limit in limits):
            raise ModelSpendLimitError("Shared model reservation budget exhausted before request")

    def reserve(self, input_tokens, output_tokens):
        if not 0 <= input_tokens <= 2_000_000 or not 1 <= output_tokens <= 4000:
            raise ModelSpendError("Invalid model token reservation")
        input_tokens += self.policy.input_overhead_tokens
        charge = self.policy.charge(input_tokens, output_tokens)
        try:
            with self.store.atomic():
                self.store._execute(
                    "UPDATE model_spend_control SET revision=revision+1 WHERE control_id=1"
                )
                self._check_owner()
                self._check_policy()
                day = math.floor(self.store.database_epoch() / 86400)
                self._check_totals(day, charge, input_tokens + output_tokens)
                identifier = str(uuid.uuid4())
                self.store._execute(
                    "INSERT INTO model_spend_reservations "
                    "(reservation_id,owner_user_id,scope_id,provider,model_id,day_number,input_tokens,output_tokens,reserved_micro_usd,policy_sha256,outcome) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        identifier,
                        self.owner_id,
                        self.scope_id,
                        self.provider,
                        self.model_id,
                        day,
                        input_tokens,
                        output_tokens,
                        charge,
                        self.policy.digest,
                        "unknown",
                    ),
                )
            return identifier
        except ModelSpendError:
            raise
        except Exception:
            raise ModelSpendError("Shared model spending admission is unavailable") from None

    def record_outcome(self, reservation_id, completed):
        # Never release on error/timeout: an outbound attempt may have been billed.
        try:
            with self.store.atomic():
                changed = self.store._execute(
                    "UPDATE model_spend_reservations SET outcome=? WHERE reservation_id=? AND owner_user_id=? AND scope_id=?",
                    (
                        "completed" if completed else "unknown",
                        reservation_id,
                        self.owner_id,
                        self.scope_id,
                    ),
                )
                if changed.rowcount != 1:
                    raise ModelSpendError("Model reservation is unavailable")
        except Exception:
            raise ModelSpendError(
                "Model reservation outcome could not be recorded; charge retained"
            ) from None


def _write_policy(store, policy, previous, source):
    store._execute(
        "UPDATE model_spend_control SET policy_sha256=?, policy_json=? WHERE control_id=1",
        (policy.digest, policy.serialized),
    )
    store._execute(
        "INSERT INTO model_spend_policy_events "
        "(event_id,previous_sha256,policy_sha256,policy_json,source,recorded_epoch) VALUES (?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            previous,
            policy.digest,
            policy.serialized,
            source,
            store.database_epoch(),
        ),
    )


def apply_policy(store, policy, expected_digest):
    """Operator-only compare-and-swap; never resets reservations or counters."""
    with store.atomic():
        store._execute("UPDATE model_spend_control SET revision=revision+1 WHERE control_id=1")
        previous = store._execute(
            "SELECT policy_sha256 FROM model_spend_control WHERE control_id=1"
        ).fetchone()["policy_sha256"]
        if (previous or "empty") != expected_digest:
            raise ModelSpendError("Shared policy changed; inspect current policy before applying")
        _write_policy(store, policy, previous, "operator_cli")
    return policy.digest
