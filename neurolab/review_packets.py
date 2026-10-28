"""Policy-masked review packets; masking does not establish independent blinding."""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from pathlib import Path

from .answer_evaluation import DIMENSIONS, _validated_reviews

NOTICE = (
    "Operational policy/model labels are withheld. Scientific wording, limitations and "
    "numerical artifacts are unchanged and may reveal the condition. Record any inferred "
    "condition or prior exposure. This packet does not establish independent human review."
)
ANSWER_FIELDS = (
    "completion_status",
    "conclusion",
    "objective",
    "refined_objective",
    "grounded_claims",
    "limitations",
    "scientific_report",
    "evidence_ids",
    "source_sha256",
    "tool_failures",
)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _masked_answer(record):
    report = record["report"]
    return copy.deepcopy(
        {
            "objective": record["task"]["objective"],
            "failure_type": record.get("failure_type"),
            "answer": {key: report[key] for key in ANSWER_FIELDS if key in report}
            if report is not None
            else None,
            "artifacts": record["artifacts"],
        }
    )


def make_review_packet(records):
    """Return separate reviewer content and confidential provenance mapping."""
    _validated_reviews(records, [])
    cases, mapping = [], []
    for record in records:
        opaque_id = str(uuid.uuid4())
        content = _masked_answer(record)
        case = {"review_id": opaque_id, **content}
        cases.append(case)
        mapping.append(
            {
                "review_id": opaque_id,
                "answer_id": record["answer_id"],
                "answer_sha256": record["answer_sha256"],
                "packet_case_sha256": _digest(case),
            }
        )
    # UUID4 identifiers already supply independent OS randomness for review order.
    cases.sort(key=lambda case: case["review_id"])
    packet = {"version": "policy-masked-v1", "notice": NOTICE, "cases": cases}
    provenance = {
        "version": "policy-masked-v1",
        "packet_sha256": _digest(packet),
        "mapping": mapping,
    }
    template = [
        {
            "review_id": case["review_id"],
            "reviewer": None,
            "reviewer_type": None,
            "blind": False,
            "ratings": dict.fromkeys(DIMENSIONS),
            "rationale": None,
            "inferred_condition": None,
            "prior_exposure": None,
        }
        for case in cases
    ]
    return packet, provenance, template


def bind_packet_reviews(records, packet, provenance, reviews):
    """Validate unchanged source/projection before translating reviews for the scorer."""
    _validated_reviews(records, [])
    if provenance["packet_sha256"] != _digest(packet):
        raise ValueError("Review packet changed")
    index = {row["answer_id"]: row for row in records}
    cases = {case["review_id"]: case for case in packet["cases"]}
    mapping = {row["review_id"]: row for row in provenance["mapping"]}
    if (
        len(cases) != len(packet["cases"])
        or len(mapping) != len(provenance["mapping"])
        or set(cases) != set(mapping)
        or len(mapping) != len(records)
    ):
        raise ValueError("Duplicate or incomplete packet mapping")
    if {row["answer_id"] for row in mapping.values()} != set(index):
        raise ValueError("Packet mapping does not cover original answers")
    for opaque_id, mapped in mapping.items():
        original = index[mapped["answer_id"]]
        expected = {"review_id": opaque_id, **_masked_answer(original)}
        if (
            mapped["answer_sha256"] != original["answer_sha256"]
            or mapped["packet_case_sha256"] != _digest(cases[opaque_id])
            or expected != cases[opaque_id]
        ):
            raise ValueError("Packet does not match original answer and evidence")
    bound, seen = [], set()
    for review in reviews:
        opaque_id = review["review_id"]
        if opaque_id not in mapping or opaque_id in seen:
            raise ValueError("Unknown or duplicate packet review")
        seen.add(opaque_id)
        mapped = mapping[opaque_id]
        bound.append(
            {**review, "answer_id": mapped["answer_id"], "answer_sha256": mapped["answer_sha256"]}
        )
    _validated_reviews(records, bound)
    return bound


def write_review_packet(records, destination):
    """Never overwrite a previous review collection; mapping must not go to reviewers."""
    packet, provenance, template = make_review_packet(records)
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, value in (
        ("reviewer-packet.json", packet),
        ("private-mapping.json", provenance),
        ("review-template.json", template),
    ):
        with (destination / name).open("x") as output:
            output.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return {"cases": len(packet["cases"]), "notice": NOTICE}
