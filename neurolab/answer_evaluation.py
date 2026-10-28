"""Recorded-answer evaluation with explicit separation of trace and semantic scores.

No inference occurs here. Semantic ratings require an identified reviewer and are
bound to the exact recorded answer and evidence; missing reviews stay unscored.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from .agent import ResearchAgent
from .evaluation import TASKS
from .research_context import (
    METHOD_TO_TOOL,
    ResearchConfiguration,
    ResearchConstraints,
    build_deterministic_plan,
)
from .store import RunStore
from .tools import SCHEMA

POLICIES = ("fixed_workflow", "seeded_random", "deterministic_replay")
DIMENSIONS = ("answers_question", "claims_supported", "scope_honest", "useful_to_researcher")
ALLOWED = tuple(SCHEMA["properties"]["action"]["enum"])
LIMIT = "Fixed twelve-question fixture set, not a random sample of research questions. Intervals describe binary ratings only; they do not establish model superiority or population performance."


def answer_digest(record):
    payload = {key: record[key] for key in ("task", "policy", "report", "artifacts", "events")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def audit_trace(report, artifacts, events):
    """Audit citation existence and action contracts, never prose entailment."""
    ids = {artifact["artifact_id"] for artifact in artifacts}
    claims = report["grounded_claims"]
    cited = sum(bool(c["evidence_ids"]) and set(c["evidence_ids"]).issubset(ids) for c in claims)
    requested = [e["payload"] for e in events if e["event_type"] == "tool.requested"]
    validator = Draft202012Validator(SCHEMA)
    valid = 0
    for call in requested:
        request = {
            "trace_id": report["run_id"],
            "hypothesis_id": call.get("hypothesis_id"),
            "dataset_id": call.get("dataset_id"),
            "action": call.get("action"),
            "parameters": call.get("parameters"),
        }
        valid += validator.is_valid(request)
    return {
        "claim_count": len(claims),
        "claims_with_existing_citations": cited,
        "requested_calls": len(requested),
        "schema_valid_calls": valid,
        "source_consistent": bool(artifacts)
        and all(a["source_sha256"] == report["source_sha256"] for a in artifacts),
        "report_evidence_ids_match": len(ids) == len(artifacts)
        and ids == set(report["evidence_ids"]),
        "scope": "Citation existence and schema validity only; no factual entailment or scientific usefulness score.",
    }


def _configuration(policy, rng, budget):
    methods = None
    if policy == "fixed_workflow":
        methods = ["dataset_profile", "compare_regimes"][:budget]
    elif policy == "seeded_random":
        methods = rng.sample(list(ALLOWED), k=budget)
    constraints = ResearchConstraints(max_steps=budget, max_tool_calls=budget, max_seconds=60)
    tool_to_method = {tool: method for method, (tool, _) in METHOD_TO_TOOL.items()}
    return ResearchConfiguration(
        preferred_methods=[tool_to_method[tool] for tool in methods or []], constraints=constraints
    )


def collect_answers(dataset, *, seed=2026, budget=2, tasks=None):
    if budget not in (1, 2):
        raise ValueError("This fixture comparison supports budgets of one or two calls")
    # Intentionally reproducible random policy; no security decisions depend on it.
    rng = random.Random(seed)  # noqa: S311
    records = []
    for task in TASKS if tasks is None else tasks:
        for policy in POLICIES:
            store = RunStore(":memory:")
            started = time.monotonic()
            record = {
                "answer_id": policy + "/" + task["task_id"],
                "task": task,
                "policy": policy,
                "seed": seed,
                "budget": budget,
                "recorded_at_utc": datetime.now(UTC).isoformat(),
                "model_id": None,
                "model_calls": 0,
                "inference_cost_usd": 0,
                "execution": "offline deterministic numeric tools; no Meta model",
                "eligible_tools": list(ALLOWED),
                "protocol": "recorded-answers-six-tools-v2",
                "report": None,
                "artifacts": [],
                "events": [],
            }
            run_id = None
            try:
                config = _configuration(policy, rng, budget)
                plan = build_deterministic_plan(task["objective"], config)
                run_id = store.create_run(
                    config.dataset_id,
                    task["objective"],
                    dataset.source_sha256,
                    seed,
                    research_configuration=config.model_dump(mode="json"),
                    research_plan=plan.model_dump(mode="json"),
                )
                result = ResearchAgent(
                    dataset,
                    store,
                    configuration=config,
                    research_plan=plan,
                    mode="replay",
                    max_steps=budget,
                    max_tool_calls=budget,
                    max_wall_time=60,
                ).run(task["objective"], seed=seed, run_id=run_id)
                report = result["report"]
                artifacts = store.list_artifacts(report["run_id"])
                events = store.list_events(report["run_id"])
                record.update(
                    report=report,
                    artifacts=artifacts,
                    events=events,
                    trace_audit=audit_trace(report, artifacts, events),
                    target_tool_present=task["target_evidence"]
                    in {a["tool_name"] for a in artifacts},
                )
            except Exception as error:
                # Record failures without leaking provider/environment exception text.
                record["failure_type"] = type(error).__name__
                if run_id:
                    record["events"] = store.list_events(run_id)
                    record["artifacts"] = store.list_artifacts(run_id)
            finally:
                record["wall_seconds"] = round(time.monotonic() - started, 6)
                store.close()
            record["answer_sha256"] = answer_digest(record)
            records.append(record)
    return records


def review_template(records):
    return [
        {
            "answer_id": r["answer_id"],
            "answer_sha256": r["answer_sha256"],
            "reviewer": None,
            "reviewer_type": None,
            "blind": False,
            "ratings": dict.fromkeys(DIMENSIONS),
            "rationale": None,
        }
        for r in records
    ]


def _wilson(successes, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - margin), min(1, center + margin)]


def _review_completed(review):
    ratings = review.get("ratings", {})
    if set(ratings) != set(DIMENSIONS):
        raise ValueError("Review dimensions do not match the rubric")
    if all(value is None for value in ratings.values()):
        return False
    if any(type(value) is not int or value not in (0, 1) for value in ratings.values()):
        raise ValueError("A completed review requires four binary ratings")
    if (
        not isinstance(review.get("reviewer"), str)
        or not review["reviewer"].strip()
        or review.get("reviewer_type") not in {"human", "assistant"}
        or not isinstance(review.get("blind"), bool)
        or not isinstance(review.get("rationale"), str)
        or not review["rationale"].strip()
    ):
        raise ValueError("Identify reviewer, type, blinding and evidence-based rationale")
    return True


def _validated_reviews(records, reviews):
    index = {r["answer_id"]: r for r in records}
    if len(index) != len(records):
        raise ValueError("Duplicate recorded answer IDs")
    if any(record["answer_sha256"] != answer_digest(record) for record in records):
        raise ValueError("Recorded answer or evidence changed")
    accepted = {}
    seen = set()
    for review in reviews:
        key = review["answer_id"]
        if key in seen or key not in index:
            raise ValueError("Unknown or duplicate reviewed answer")
        seen.add(key)
        record = index[key]
        if review["answer_sha256"] != record["answer_sha256"]:
            raise ValueError("Review does not match the recorded answer and evidence")
        if _review_completed(review):
            accepted[key] = review
    return accepted


def _trace_totals(rows):
    audits = [
        audit_trace(row["report"], row["artifacts"], row["events"])
        for row in rows
        if row["report"] is not None
    ]
    requested = sum(a["requested_calls"] for a in audits)
    valid = sum(a["schema_valid_calls"] for a in audits)
    claims = sum(a["claim_count"] for a in audits)
    cited = sum(a["claims_with_existing_citations"] for a in audits)
    return {
        "audited_reports": len(audits),
        "requested_calls_in_audited_reports": requested,
        "schema_valid_calls": valid,
        "schema_valid_fraction": valid / requested if requested else None,
        "claims_in_audited_reports": claims,
        "claims_with_existing_citations": cited,
        "citation_exists_fraction": cited / claims if claims else None,
        "source_consistent_reports": sum(a["source_consistent"] for a in audits),
        "scope": "Only reports with completed trace audits; reportless failures remain separately counted. No semantic entailment score.",
    }


def summarize_answers(records, reviews=()):
    if any(record["policy"] not in POLICIES for record in records):
        raise ValueError(
            "Live matrix requires seed-aware scoring; offline scorer cannot score these policies"
        )
    accepted = _validated_reviews(records, reviews)
    summary = {
        "version": "recorded-answers-v1",
        "record_count": len(records),
        "semantic_reviews_completed": len(accepted),
        "semantic_reviews_pending": len(records) - len(accepted),
        "model_comparison": "NOT RUN: Meta credits exhausted; inference intentionally paused",
        "reviewers": sorted({r["reviewer"] for r in accepted.values()}),
        "interval_scope": LIMIT,
        "policies": {},
    }
    for policy in POLICIES:
        rows = [r for r in records if r["policy"] == policy]
        rated = [accepted[r["answer_id"]] for r in rows if r["answer_id"] in accepted]
        dimensions = {}
        for dimension in DIMENSIONS:
            successes = sum(review["ratings"][dimension] for review in rated)
            dimensions[dimension] = {
                "positive_ratings": successes,
                "reviewed": len(rated),
                "fraction": successes / len(rated) if rated else None,
                "wilson_95_interval": _wilson(successes, len(rated)),
            }
        summary["policies"][policy] = {
            "tasks_recorded": len(rows),
            "trace_metrics": _trace_totals(rows),
            "execution_failures": sum(r["report"] is None for r in rows),
            "target_tool_present": sum(
                r["task"]["target_evidence"] in {a["tool_name"] for a in r["artifacts"]}
                for r in rows
            ),
            "target_tool_scope": "Action coverage, not answer accuracy",
            "wall_seconds_total": sum(r["wall_seconds"] for r in rows),
            "model_calls": 0,
            "inference_cost_usd": 0,
            "semantic_ratings": dimensions,
            "reviewer_types": sorted({r["reviewer_type"] for r in rated}),
            "all_reviews_blind": bool(rated) and all(r["blind"] for r in rated),
        }
    return summary


def write_answer_evaluation(dataset, output: Path, *, seed=2026, budget=2):
    output.mkdir(parents=True, exist_ok=False)
    records = collect_answers(dataset, seed=seed, budget=budget)
    (output / "tasks.json").write_text(json.dumps(TASKS, indent=2) + "\n")
    (output / "results.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in records)
    )
    (output / "review-template.json").write_text(
        json.dumps(review_template(records), indent=2) + "\n"
    )
    summary = summarize_answers(records)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
