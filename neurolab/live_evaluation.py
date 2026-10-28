"""Fail-closed collector for the frozen known-set comparison, not a quality score."""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from datetime import UTC, datetime
from pathlib import Path

from .agent import ResearchAgent
from .answer_evaluation import ALLOWED, _configuration, answer_digest, audit_trace, review_template
from .evaluation import TASKS
from .model_spend import SpendPolicy
from .provenance import RUNTIME_PROVENANCE
from .providers import ModelProviderError, OpenAICompatibleAdapter
from .research_context import (
    METHOD_TO_TOOL,
    ResearchConfiguration,
    ResearchConstraints,
    build_deterministic_plan,
)

POLICIES = (
    "meta_with_results",
    "meta_without_result_evidence",
    "deterministic_focused",
    "fixed_profile_then_contrast",
    "seeded_random_without_replacement",
)
SEEDS = (2026, 77, 113)


def trial_matrix():
    return [
        {"task": task, "seed": seed, "policy": policy}
        for task in TASKS
        for seed in SEEDS
        for policy in POLICIES
    ]


def trial_configuration(trial):
    policy, seed = trial["policy"], trial["seed"]
    if policy.startswith("meta_"):
        return ResearchConfiguration(
            preferred_methods=list(METHOD_TO_TOOL),
            constraints=ResearchConstraints(max_steps=2, max_tool_calls=2, max_seconds=60),
        )
    mapping = {
        "deterministic_focused": "deterministic_replay",
        "fixed_profile_then_contrast": "fixed_workflow",
        "seeded_random_without_replacement": "seeded_random",
    }
    # Scientific baseline randomization only; never a credential or security decision.
    rng = random.Random(f"{seed}:{trial['task']['task_id']}")  # noqa: S311
    return _configuration(mapping[policy], rng, 2)


def validate_live_protocol(manifest, dataset, store, owner, root):
    """No network, output creation, inference or automatic policy change on failure."""
    user = store.get_user(owner)
    if not user or not user["is_active"]:
        raise ValueError("Live collection requires a verified active server owner")
    if (
        manifest.get("status") != "APPROVED FOR COLLECTION"
        or manifest.get("policies") != list(POLICIES)
        or manifest.get("seeds") != list(SEEDS)
        or manifest.get("accuracy_tasks") != [t["task_id"] for t in TASKS]
        or manifest.get("utility_tasks") != [t["task_id"] for t in TASKS[:10]]
        or manifest.get("planned_research_trials") != 180
        or manifest.get("planned_meta_trials") != 72
        or manifest.get("per_trial_maxima") != {"numeric_calls": 2, "steps": 2, "wall_seconds": 60}
    ):
        raise ValueError("Unapproved or changed evaluation matrix")
    root = Path(root).resolve()
    required = tuple(
        str(path.relative_to(root)) for path in sorted((root / "neurolab").glob("*.py"))
    ) + (
        "requirements.txt",
        "scripts/collect_live_evaluation.py",
        "schemas/agent_tool_call.schema.json",
        "neurolab/live_evaluation.py",
        "neurolab/agent.py",
        "neurolab/providers.py",
        "neurolab/model_spend.py",
        "neurolab/research_context.py",
        "neurolab/tools.py",
        "neurolab/action_selection.py",
        "neurolab/model_evidence.py",
        "eval/tasks.json",
        "data/raw/ghana/maize_combined_phenotypes.csv",
    )
    frozen = manifest.get("input_sha256", {})
    if not set(required).issubset(frozen):
        raise ValueError("Protocol must freeze collector, model context and scientific inputs")
    for relative, digest in frozen.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen evaluation input changed")
    if any(
        frozen.get(name) != digest for name, digest in RUNTIME_PROVENANCE["module_sha256"].items()
    ):
        raise ValueError("Frozen inputs differ from loaded runtime source")
    if frozen[required[-1]] != dataset.source_sha256:
        raise ValueError("Loaded source differs from frozen source")
    policy = SpendPolicy.from_environment()
    if (
        manifest.get("spend_policy_sha256") != policy.digest
        or manifest.get("model_id") != policy.model_id
        or manifest.get("provider_account_controls_verified") is not True
        or manifest.get("owner_authorized") is not True
        or manifest.get("approved_utc_day") != datetime.now(UTC).date().isoformat()
        or manifest.get("approved_spend_cap_micro_usd", 0) < policy.global_day_micro_usd
    ):
        raise ValueError("Reviewed model, aggregate daily budget or authorization is missing")
    row = store._execute(
        "SELECT policy_sha256 FROM model_spend_control WHERE control_id=1"
    ).fetchone()
    if row["policy_sha256"] not in (None, policy.digest):
        raise ValueError("Shared spending policy differs; no automatic policy migration")
    # Adapter startup validates the enabled flag, verified model and bounded generation settings.
    adapter = OpenAICompatibleAdapter.from_environment()
    if manifest.get("max_output_tokens") != adapter.max_output_tokens:
        raise ValueError("Generation settings differ from the frozen protocol")
    return policy


def _append(path, value):
    with path.open("a") as output:
        output.write(
            json.dumps({"recorded_at_utc": datetime.now(UTC).isoformat(), **value}, allow_nan=False)
            + "\n"
        )
        output.flush()
        os.fsync(output.fileno())


class RecordedAdapter(OpenAICompatibleAdapter):
    """Record actual JSON bodies/responses after the standard SQL spending guard."""

    def _send_structured(self, endpoint, body, timeout):
        if datetime.now(UTC).date().isoformat() != self.approved_utc_day:
            raise ModelProviderError("Evaluation daily approval expired before transport")
        self.requests_attempted = getattr(self, "requests_attempted", 0) + 1
        _append(
            self.transcript,
            {"kind": "provider.request", "run_id": self.evaluation_run_id, "body": body},
        )
        try:
            response = super()._send_structured(endpoint, body, timeout)
        except BaseException as error:
            self._record_response_metadata()
            if isinstance(error, ModelProviderError) and error.permanent:
                self.permanent_failure_status = error.http_status
            _append(
                self.transcript,
                {
                    "kind": "provider.failure",
                    "run_id": self.evaluation_run_id,
                    "error_type": type(error).__name__,
                    "http_status": getattr(error, "http_status", None),
                },
            )
            raise
        self._record_response_metadata()
        return response

    def _record_response_metadata(self):
        metadata = self._last_response_metadata
        if metadata is None:
            return
        _append(
            self.transcript,
            {"kind": "provider.response", "run_id": self.evaluation_run_id, **metadata},
        )
        body = metadata.get("body")
        usage = body.get("usage") if isinstance(body, dict) else None
        self.reported_usage = [*getattr(self, "reported_usage", []), usage]


def execute_live_trial(trial, dataset, store, owner, transcript):
    config = trial_configuration(trial)
    objective = trial["task"]["objective"]
    plan = build_deterministic_plan(objective, config)
    run_id = store.create_run(
        config.dataset_id,
        objective,
        dataset.source_sha256,
        trial["seed"],
        owner_user_id=owner,
        research_configuration=config.model_dump(mode="json"),
        research_plan=plan.model_dump(mode="json"),
    )
    _append(
        transcript,
        {
            "kind": "trial.run_created",
            "run_id": run_id,
            "policy": trial["policy"],
            "seed": trial["seed"],
            "task_id": trial["task"]["task_id"],
        },
    )
    adapter = None
    try:
        if trial["policy"].startswith("meta_"):
            adapter = RecordedAdapter.from_environment().bind_spending(
                store, owner, "run:" + run_id
            )
            adapter.transcript = transcript
            adapter.evaluation_run_id = run_id
            adapter.approved_utc_day = trial["approved_utc_day"]
        ResearchAgent(
            dataset,
            store,
            mode="meta" if adapter else "replay",
            model_adapter=adapter,
            model_feedback=trial["policy"] != "meta_without_result_evidence",
            configuration=config,
            research_plan=plan,
            max_steps=2,
            max_tool_calls=2,
            max_wall_time=60,
        ).run(objective, seed=trial["seed"], run_id=run_id)
    except BaseException as error:
        store.set_stage(
            run_id,
            "FAILED",
            "Evaluation execution failed or was interrupted; retained evidence is not a complete answer",
        )
        store.add_event(run_id, "run.failed", {"error_type": type(error).__name__})
        snapshot = _trial_snapshot(store, run_id, adapter)
        snapshot["failure_type"] = type(error).__name__
        if isinstance(error, Exception):
            return snapshot
        error.evaluation_evidence = snapshot
        raise
    return _trial_snapshot(store, run_id, adapter)


def _trial_snapshot(store, run_id, adapter):
    report = store.get_run(run_id)["report"]
    artifacts, events = store.list_artifacts(run_id), store.list_events(run_id)
    reservations = [
        dict(row)
        for row in store._execute(
            "SELECT input_tokens,output_tokens,reserved_micro_usd,outcome FROM model_spend_reservations WHERE scope_id=?",
            ("run:" + run_id,),
        ).fetchall()
    ]
    snapshot = {
        "run_id": run_id,
        "report": report,
        "artifacts": artifacts,
        "events": events,
        "tokens_reserved": adapter.tokens_reserved if adapter else 0,
        "model_calls": getattr(adapter, "requests_attempted", 0),
        "provider_reported_usage": getattr(adapter, "reported_usage", []),
        "permanent_provider_failure_status": getattr(adapter, "permanent_failure_status", None),
        "spend_reservations": reservations,
        "cost_scope": "Conservative reservations, not invoices",
    }
    if report is not None:
        snapshot["trace_audit"] = audit_trace(report, artifacts, events)
    return snapshot


def collect_live_matrix(
    manifest, dataset, store, owner, destination, root, *, runner=execute_live_trial
):
    validate_live_protocol(manifest, dataset, store, owner, root)
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    (destination / "protocol.json").write_text(json.dumps(manifest, indent=2) + "\n")
    records = []
    for trial in trial_matrix():
        trial = {**trial, "approved_utc_day": manifest["approved_utc_day"]}
        if datetime.now(UTC).date().isoformat() != manifest["approved_utc_day"]:
            raise ValueError("Daily approval expired; prior attempts retained, no automatic resume")
        identifier = f"{trial['policy']}/{trial['seed']}/{trial['task']['task_id']}"
        _append(
            destination / "attempts.jsonl",
            {
                "kind": "trial.started",
                "answer_id": identifier,
                "utc": datetime.now(UTC).isoformat(),
            },
        )
        started = time.monotonic()
        record = {
            **trial,
            "answer_id": identifier,
            "protocol": manifest["protocol_id"],
            "budget": 2,
            "eligible_tools": list(ALLOWED),
            "report": None,
            "artifacts": [],
            "events": [],
            "model_id": manifest["model_id"] if trial["policy"].startswith("meta_") else None,
        }
        interrupted = False
        try:
            record.update(runner(trial, dataset, store, owner, destination / "provider.jsonl"))
        except BaseException as error:
            record.update(getattr(error, "evaluation_evidence", {}))
            record["failure_type"] = type(error).__name__
            interrupted = not isinstance(error, Exception)
            if interrupted:
                raise
        finally:
            record["wall_seconds"] = round(time.monotonic() - started, 6)
            record["interrupted"] = interrupted
            record["answer_sha256"] = answer_digest(record)
            _append(destination / "results.jsonl", record)
            records.append(record)
        if record.get("permanent_provider_failure_status") is not None:
            _append(
                destination / "attempts.jsonl",
                {
                    "kind": "collection.stopped",
                    "answer_id": identifier,
                    "reason": "permanent_provider_failure",
                    "http_status": record["permanent_provider_failure_status"],
                    "utc": datetime.now(UTC).isoformat(),
                },
            )
            raise ValueError(
                "Permanent provider failure; partial evidence retained, no automatic resume"
            )
    (destination / "review-template.json").write_text(
        json.dumps(review_template(records), indent=2) + "\n"
    )
    return {
        "records": len(records),
        "meta_trials": sum(r["model_id"] is not None for r in records),
        "semantic_reviews_completed": 0,
        "scope": "Known-set collection only; no quality score or winner claim",
    }
