"""Question-clustered summaries of recorded trials; no automatic semantic judgment."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from fractions import Fraction

from .answer_evaluation import DIMENSIONS, _trace_totals, _validated_reviews
from .evaluation import TASKS
from .live_evaluation import POLICIES, SEEDS

INTERVAL_SCOPE = (
    "Exact percentile bootstrap distribution of question-level means. Seeds stay "
    "within their question. Descriptive variation on this fixed known question set; "
    "not population accuracy, independent observations or evidence of superiority."
)
FAILURE_DIMENSIONS = {"answers_question", "useful_to_researcher"}


def _cells(records):
    tasks = {task["task_id"]: task for task in TASKS}
    cells = {}
    for row in records:
        key = (row["policy"], row["task"]["task_id"], row["seed"])
        policy, task_id, seed = key
        if (
            policy not in POLICIES
            or task_id not in tasks
            or type(seed) is not int
            or seed not in SEEDS
            or row["task"] != tasks[task_id]
            or row["answer_id"] != f"{policy}/{seed}/{task_id}"
            or row["budget"] != 2
        ):
            raise ValueError("Record differs from the declared task/seed/policy matrix")
        if key in cells:
            raise ValueError("Duplicate task/seed/policy cell")
        report = row["report"]
        if report is not None and (
            report["objective"] != row["task"]["objective"]
            or report["seed"] != seed
            or type(report["tool_calls"]) is not int
            or not 0 <= report["tool_calls"] <= 2
        ):
            raise ValueError("Report differs from recorded objective, seed or call budget")
        _validate_observations(row)
        cells[key] = row
    return cells


def _validate_observations(row):
    if "model_calls" in row and (
        type(row["model_calls"]) is not int or not 0 <= row["model_calls"] <= 2
    ):
        raise ValueError("Invalid observed model-call count")
    elapsed = row.get("wall_seconds")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("Invalid observed elapsed time")
    for reservation in row.get("spend_reservations", []):
        charge = reservation.get("reserved_micro_usd")
        if (
            type(charge) is not int
            or charge < 0
            or reservation.get("outcome") not in {"completed", "unknown"}
        ):
            raise ValueError("Invalid observed spending reservation")


def _trial_rating(row, accepted, dimension):
    if row is None:
        return {"basis": "not_attempted", "value": None}
    if row["report"] is None:
        return (
            {"basis": "automatic_no_answer_zero", "value": 0}
            if dimension in FAILURE_DIMENSIONS
            else {"basis": "no_output_unassessed", "value": None}
        )
    review = accepted.get(row["answer_id"])
    if review is None:
        return {"basis": "pending_review", "value": None}
    return {"basis": "identified_review", "value": review["ratings"][dimension]}


def _question_dimension(cells, accepted, policy, task, dimension):
    results = [
        {
            "seed": seed,
            **_trial_rating(cells.get((policy, task["task_id"], seed)), accepted, dimension),
        }
        for seed in SEEDS
    ]
    counts = Counter(row["basis"] for row in results)
    values = [row["value"] for row in results if row["value"] is not None]
    missing, pending = counts["not_attempted"], counts["pending_review"]
    return {
        "question_mean": statistics.fmean(values) if values and not (missing or pending) else None,
        "scored_trials": len(values),
        "positive_ratings": sum(values),
        "automatic_no_answer_zeros": counts["automatic_no_answer_zero"],
        "reportless_excluded": counts["no_output_unassessed"],
        "pending_review": pending,
        "missing_trials": missing,
        "expected_seeds": len(SEEDS),
        "seed_results": results,
    }


def _exact_question_interval(values):
    """Integer-weighted distribution of n draws from n question means."""
    frequency = Counter(values)
    distribution = {Fraction(0): 1}
    for _ in values:
        following = Counter()
        for total, weight in distribution.items():
            for value, multiplicity in frequency.items():
                following[total + value] += weight * multiplicity
        distribution = following
    sequence_count = len(values) ** len(values)
    cumulative, lower, upper = 0, None, None
    for total, weight in sorted(distribution.items()):
        cumulative += weight
        if lower is None and cumulative * 40 >= sequence_count:
            lower = float(total / len(values))
        if cumulative * 40 >= sequence_count * 39:
            upper = float(total / len(values))
            break
    return [lower, upper]


def _question_aggregate(rows):
    eligible = [
        row
        for row in rows
        if row["scored_trials"] or row["pending_review"] or row["missing_trials"]
    ]
    complete = bool(eligible) and all(row["question_mean"] is not None for row in eligible)
    values = (
        [Fraction(row["positive_ratings"], row["scored_trials"]) for row in eligible]
        if complete
        else []
    )
    return {
        "question_macro_mean": statistics.fmean(values) if values else None,
        "question_bootstrap_95_interval": _exact_question_interval(values) if values else None,
        "interval_scope": INTERVAL_SCOPE,
        "bootstrap_method": "Exact weighted discrete distribution; inverse-CDF2.5/97.5percentiles",
        "bootstrap_resample_size": len(values) if values else None,
        "expected_questions": len(rows),
        "eligible_questions": len(eligible),
        "scored_questions": sum(row["question_mean"] is not None for row in rows),
        "reportless_excluded_trials": sum(row["reportless_excluded"] for row in rows),
        "automatic_no_answer_zeros": sum(row["automatic_no_answer_zeros"] for row in rows),
        "pending_review": sum(row["pending_review"] for row in rows),
        "missing_trials": sum(row["missing_trials"] for row in rows),
    }


def _observed_totals(rows):
    known_calls = [r["model_calls"] for r in rows if type(r.get("model_calls")) is int]
    reservations = [r for row in rows for r in row.get("spend_reservations", [])]
    missing_calls = len(rows) - len(known_calls)
    unknown_cost = sum("spend_reservations" not in r for r in rows)
    return {
        "model_calls": sum(known_calls) if not missing_calls else None,
        "known_model_calls_subtotal": sum(known_calls),
        "unknown_call_count_records": missing_calls,
        "reserved_micro_usd": sum(r["reserved_micro_usd"] for r in reservations)
        if not unknown_cost
        else None,
        "known_reserved_micro_usd_subtotal": sum(r["reserved_micro_usd"] for r in reservations),
        "unknown_reservation_records": unknown_cost,
        "reservation_outcomes": dict(Counter(r["outcome"] for r in reservations)),
        "invoice_cost_usd": None,
        "cost_scope": "Reservations are conservative admission, not invoices",
        "wall_seconds_total": sum(r["wall_seconds"] for r in rows),
        "reportless_failures": sum(r["report"] is None for r in rows),
    }


def summarize_live_answers(records, reviews=()):
    accepted = _validated_reviews(records, reviews)
    cells = _cells(records)
    for row in records:
        review = accepted.get(row["answer_id"])
        if (
            row["report"] is None
            and review
            and any(review["ratings"][d] for d in FAILURE_DIMENSIONS)
        ):
            raise ValueError(
                "A missing answer cannot receive positive direct-answer/usefulness ratings"
            )
    policies = {}
    for policy in POLICIES:
        questions = [
            {
                "task_id": task["task_id"],
                "dimensions": {
                    dimension: _question_dimension(cells, accepted, policy, task, dimension)
                    for dimension in DIMENSIONS
                },
            }
            for task in TASKS
        ]
        policies[policy] = {
            "observed_trials": sum(key[0] == policy for key in cells),
            "expected_trials": len(TASKS) * len(SEEDS),
            "questions": questions,
            "accuracy_all_12": {
                d: _question_aggregate([q["dimensions"][d] for q in questions]) for d in DIMENSIONS
            },
            "utility_first_10": {
                d: _question_aggregate([q["dimensions"][d] for q in questions[:10]])
                for d in DIMENSIONS
            },
            "operational_totals": _observed_totals([r for r in records if r["policy"] == policy]),
            "trace_metrics": _trace_totals([r for r in records if r["policy"] == policy]),
            "requested_tool_calls_all_records": sum(
                e["event_type"] == "tool.requested"
                for r in records
                if r["policy"] == policy
                for e in r["events"]
            ),
            "artifacts_all_records": sum(
                len(r["artifacts"]) for r in records if r["policy"] == policy
            ),
        }
    return {
        "version": "known-set-question-clustered-v1",
        "record_count": len(records),
        "expected_records": len(TASKS) * len(SEEDS) * len(POLICIES),
        "collection_complete": len(cells) == 180,
        "reviews_completed": len(accepted),
        "report_outputs_unreviewed": sum(
            r["report"] is not None and r["answer_id"] not in accepted for r in records
        ),
        "reviewer_types": sorted({r["reviewer_type"] for r in accepted.values()}),
        "reviewers_claim_blind": bool(accepted) and all(r["blind"] for r in accepted.values()),
        "independence_verified": False,
        "held_out": False,
        "winner": None,
        "scope": "Scores require identified evidence-bound reviewers. Fixed known-set, dependent questions; no automatic groundedness or superiority claim.",
        "policies": policies,
    }
