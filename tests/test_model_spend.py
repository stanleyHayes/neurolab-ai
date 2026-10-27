"""Synthetic pricing and transport fixtures; actual shared SQL admission."""

import json
import os
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import patch

from neurolab.model_spend import (
    ModelSpendError,
    ModelSpendGuard,
    ModelSpendLimitError,
    SpendPolicy,
    apply_policy,
)
from neurolab.providers import ModelProviderError, OpenAICompatibleAdapter, adapter_status
from neurolab.store import RunStore
from tests.isolated_database import isolated_database
from tests.test_providers import SPEND_ENV


class SharedModelSpendTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        database = isolated_database(temporary.name)
        self.path = database.__enter__()
        self.addCleanup(database.__exit__, None, None, None)
        self.store = RunStore(self.path)
        self.addCleanup(lambda: self.store.close())
        self.owner = self.store.create_user("spend@example.test", "store-fixture", "Test")[
            "user_id"
        ]
        self.other = self.store.create_user("other@example.test", "store-fixture", "Other")[
            "user_id"
        ]
        with patch.dict(os.environ, SPEND_ENV, clear=True):
            self.policy = SpendPolicy.from_environment()

    def guard(self, *, store=None, owner=None, scope=None, policy=None):
        return ModelSpendGuard(
            store or self.store,
            owner or self.owner,
            scope or "refine:" + str(uuid.uuid4()),
            "meta",
            "fixture",
            policy or self.policy,
        )

    def rows(self):
        with self.store._lock:
            return [
                dict(row)
                for row in self.store._execute("SELECT * FROM model_spend_reservations").fetchall()
            ]

    def test_concurrent_connections_cannot_oversubscribe_global_money(self):
        policy = replace(self.policy, global_day_micro_usd=363)
        barrier = threading.Barrier(6)

        def reserve(_):
            store = RunStore(self.path)
            try:
                barrier.wait()
                with patch.object(store, "database_epoch", return_value=120):
                    try:
                        self.guard(store=store, policy=policy).reserve(100, 10)
                        return True
                    except ModelSpendLimitError:
                        return False
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            accepted = list(pool.map(reserve, range(6)))
        self.assertEqual(sum(accepted), 3)
        self.assertEqual(sum(row["reserved_micro_usd"] for row in self.rows()), 363)
        self.assertTrue(all(row["outcome"] == "unknown" for row in self.rows()))

    def test_run_owner_global_and_utc_rollover_are_separate(self):
        policy = replace(
            self.policy, run_micro_usd=242, owner_day_micro_usd=363, global_day_micro_usd=484
        )
        scope = "refine:fixed"
        guard = self.guard(scope=scope, policy=policy)
        with patch.object(self.store, "database_epoch", return_value=86399):
            guard.reserve(100, 10)
            guard.reserve(100, 10)
            candidate = self.guard(scope=scope, policy=policy)
            with self.assertRaises(ModelSpendLimitError):
                candidate.reserve(100, 10)
            self.guard(policy=policy).reserve(100, 10)
            candidate = self.guard(policy=policy)
            with self.assertRaises(ModelSpendLimitError):
                candidate.reserve(100, 10)
            self.guard(owner=self.other, policy=policy).reserve(100, 10)
            candidate = self.guard(owner=self.other, policy=policy)
            with self.assertRaises(ModelSpendLimitError):
                candidate.reserve(100, 10)
        with patch.object(self.store, "database_epoch", return_value=86400):
            self.guard(policy=policy).reserve(100, 10)
            with self.assertRaises(ModelSpendLimitError):
                guard.reserve(100, 10)
        self.assertEqual(len(self.rows()), 5)

    def test_unknown_and_completed_reservations_survive_restart_without_refund(self):
        policy = replace(self.policy, global_day_micro_usd=242)
        with patch.object(self.store, "database_epoch", return_value=120):
            guard = self.guard(policy=policy)
            first = guard.reserve(100, 10)
            guard.record_outcome(first, False)
            second = guard.reserve(100, 10)
            guard.record_outcome(second, True)
        self.store.close()
        self.store = RunStore(self.path)
        candidate = self.guard(policy=policy)
        with (
            patch.object(self.store, "database_epoch", return_value=120),
            self.assertRaises(ModelSpendLimitError),
        ):
            candidate.reserve(100, 10)
        self.assertEqual({row["outcome"] for row in self.rows()}, {"unknown", "completed"})
        self.assertEqual(sum(row["reserved_micro_usd"] for row in self.rows()), 242)

    def test_operator_policy_change_is_audited_without_resetting_reservations(self):
        self.guard().reserve(100, 10)
        changed = replace(self.policy, run_micro_usd=self.policy.run_micro_usd + 1)
        with self.assertRaises(ModelSpendError):
            apply_policy(self.store, changed, "empty")
        self.assertEqual(apply_policy(self.store, changed, self.policy.digest), changed.digest)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]["reserved_micro_usd"], 121)
        with self.store._lock:
            events = self.store._execute("SELECT source FROM model_spend_policy_events").fetchall()
        self.assertEqual({row["source"] for row in events}, {"first_admission", "operator_cli"})
        candidate = self.guard()
        with self.assertRaises(ModelSpendError):
            candidate.reserve(100, 10)

    def test_changed_transport_model_or_endpoint_cannot_use_approved_prices(self):
        for changes in (
            {"model_id": "different"},
            {"endpoint": "https://other.invalid"},
            {"provider": "other"},
        ):
            model = OpenAICompatibleAdapter(
                SPEND_ENV["META_MODEL_API_BASE_URL"],
                "fixture",
                "fixture",
                provider="meta",
                spend_guard=self.guard(),
            )
            for key, value in changes.items():
                setattr(model, key, value)
            with (
                self.subTest(changes=changes),
                patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "true"}),
                patch("neurolab.providers.http.client.HTTPSConnection") as transport,
            ):
                with self.assertRaises(ModelProviderError):
                    model.generate_structured([], {"type": "object"}, timeout=1)
                transport.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_more_generous_replica_policy_fails_closed(self):
        self.guard().reserve(100, 10)
        changed = replace(self.policy, global_day_micro_usd=self.policy.global_day_micro_usd + 1)
        candidate = self.guard(policy=changed)
        with self.assertRaisesRegex(ModelSpendError, "differs"):
            candidate.reserve(100, 10)
        self.assertEqual(len(self.rows()), 1)

    def test_inactive_unowned_and_cross_owner_scopes_cannot_spend(self):
        run = self.store.create_run(
            "ghana_combined", "owned", "source", 1, owner_user_id=self.other
        )
        candidate = self.guard(scope="run:" + run)
        with self.assertRaises(ModelSpendError):
            candidate.reserve(100, 10)
        legacy = self.store.create_run("ghana_combined", "legacy", "source", 1)
        candidate = self.guard(scope="run:" + legacy)
        with self.assertRaises(ModelSpendError):
            candidate.reserve(100, 10)
        with self.store.atomic():
            self.store._execute("UPDATE users SET is_active=0 WHERE user_id=?", (self.owner,))
        candidate = self.guard()
        with self.assertRaises(ModelSpendError):
            candidate.reserve(100, 10)
        self.assertEqual(self.rows(), [])

    def test_sql_token_reservations_are_shared_across_adapter_instances(self):
        policy = replace(self.policy, run_tokens=121)
        scope = "refine:tokens"
        self.guard(scope=scope, policy=policy).reserve(100, 10)
        candidate = self.guard(scope=scope, policy=policy)
        with self.assertRaises(ModelSpendLimitError):
            candidate.reserve(1, 10)
        self.assertEqual(len(self.rows()), 1)

    def test_money_rounds_up_without_float_arithmetic_and_stores_no_prompts(self):
        policy = replace(
            self.policy, input_usd_per_million="0.0001", output_usd_per_million="0.0001"
        )
        self.guard(policy=policy).reserve(1, 1)
        row = self.rows()[0]
        self.assertEqual(row["reserved_micro_usd"], 1)
        self.assertEqual(row["input_tokens"], 2)
        self.assertNotIn("prompt", json.dumps(row))
        self.assertNotIn("api_key", json.dumps(row))

    def test_database_failure_is_sanitized_before_transport(self):
        model = OpenAICompatibleAdapter(
            SPEND_ENV["META_MODEL_API_BASE_URL"],
            "fixture",
            "fixture",
            provider="meta",
            spend_guard=self.guard(),
        )
        with (
            patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "true"}),
            patch.object(self.store, "_execute", side_effect=RuntimeError("private db secret")),
            patch("neurolab.providers.http.client.HTTPSConnection") as transport,
            self.assertRaisesRegex(ModelProviderError, "unavailable") as error,
        ):
            model.generate_structured([], {"type": "object"}, timeout=1)
        self.assertNotIn("secret", str(error.exception))
        transport.assert_not_called()
        self.assertEqual(model.tokens_reserved, 0)

    def test_budget_denial_never_constructs_a_network_connection(self):
        policy = replace(self.policy, run_micro_usd=1)
        model = OpenAICompatibleAdapter(
            SPEND_ENV["META_MODEL_API_BASE_URL"],
            "fixture",
            "fixture",
            provider="meta",
            spend_guard=self.guard(policy=policy),
        )
        with (
            patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "true"}),
            patch("neurolab.providers.http.client.HTTPSConnection") as transport,
            self.assertRaisesRegex(ModelProviderError, "budget exhausted"),
        ):
            model.generate_structured([], {"type": "object"}, timeout=1)
        transport.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_transport_constructor_failure_retains_unknown_charge(self):
        model = OpenAICompatibleAdapter(
            SPEND_ENV["META_MODEL_API_BASE_URL"],
            "fixture",
            "fixture",
            provider="meta",
            spend_guard=self.guard(),
        )
        with (
            patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "true"}),
            patch(
                "neurolab.providers.http.client.HTTPSConnection",
                side_effect=OSError("private secret"),
            ),
            self.assertRaisesRegex(ModelProviderError, "could not be reached"),
        ):
            model.generate_structured([], {"type": "object"}, timeout=1)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]["outcome"], "unknown")


class SpendingConfigurationTests(unittest.TestCase):
    def test_missing_zero_negative_infinite_and_overprecise_settings_fail_closed(self):
        for changes in (
            {},
            {"MODEL_MAX_COST_USD": "0"},
            {"MODEL_MAX_COST_USD": "-1"},
            {"MODEL_INPUT_USD_PER_MILLION_TOKENS": "NaN"},
            {"MODEL_OUTPUT_USD_PER_MILLION_TOKENS": "Infinity"},
            {"MODEL_OWNER_DAILY_COST_USD": "0.0000001"},
            {"MODEL_INPUT_OVERHEAD_TOKENS": "0"},
        ):
            values = {**SPEND_ENV, **changes} if changes else {}
            with self.subTest(changes=changes), patch.dict(os.environ, values, clear=True):
                with self.assertRaises(ModelSpendError):
                    SpendPolicy.from_environment()
                self.assertFalse(adapter_status()["enabled_for_runs"])

    def test_operator_smoke_respects_pause_before_database_or_transport(self):
        import contextlib
        import io

        from scripts.smoke_meta_provider import main

        with (
            patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "false"}, clear=True),
            patch("scripts.smoke_meta_provider.RunStore") as database,
            patch("neurolab.providers.http.client.HTTPSConnection") as transport,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(), 1)
        database.assert_not_called()
        transport.assert_not_called()

    def test_adapter_without_owned_guard_cannot_use_transport(self):
        model = OpenAICompatibleAdapter("https://provider.invalid", "fixture", "fixture")
        with patch("neurolab.providers.http.client.HTTPSConnection") as transport:
            with self.assertRaisesRegex(ModelProviderError, "shared owner"):
                model.generate_structured([], {"type": "object"}, timeout=1)
            transport.assert_not_called()
