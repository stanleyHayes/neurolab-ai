"""Actual offline numeric evidence; fixture human labels do not establish review."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from neurolab.answer_evaluation import DIMENSIONS, collect_answers
from neurolab.evaluation import TASKS
from neurolab.ghana import load_ghana
from neurolab.review_packets import (
    _digest,
    bind_packet_reviews,
    make_review_packet,
    write_review_packet,
)


class ReviewPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = collect_answers(load_ghana(), tasks=TASKS[:1], budget=1)

    def test_projection_preserves_science_without_operational_labels_or_mutation(self):
        original = copy.deepcopy(self.records)
        packet, mapping, template = make_review_packet(self.records)
        self.assertEqual(self.records, original)
        self.assertEqual(len(packet["cases"]), 3)
        index = {row["answer_id"]: row for row in self.records}
        for row in mapping["mapping"]:
            case = next(c for c in packet["cases"] if c["review_id"] == row["review_id"])
            source = index[row["answer_id"]]
            self.assertEqual(case["artifacts"], source["artifacts"])
            self.assertEqual(case["answer"]["limitations"], source["report"]["limitations"])
            self.assertEqual(case["answer"]["conclusion"], source["report"]["conclusion"])
            self.assertNotIn("policy", case)
            self.assertNotIn("mode", case["answer"])
            self.assertNotIn("model_id", case["answer"])
        self.assertTrue(all(row["reviewer"] is None for row in template))
        self.assertEqual(
            bind_packet_reviews(self.records, packet, mapping, template)[0]["ratings"],
            dict.fromkeys(DIMENSIONS),
        )

    def test_packet_edits_cannot_mutate_original_numeric_evidence(self):
        original = copy.deepcopy(self.records)
        packet, _, _ = make_review_packet(self.records)
        packet["cases"][0]["artifacts"][0]["warnings"].append("Fixture edit")
        self.assertEqual(self.records, original)

    def test_failure_without_answer_is_retained(self):
        from neurolab.answer_evaluation import answer_digest

        record = copy.deepcopy(self.records[0])
        record.update(report=None, failure_type="FixtureFailure", artifacts=[], events=[])
        record["answer_sha256"] = answer_digest(record)
        packet, _, _ = make_review_packet([record])
        self.assertEqual(packet["cases"][0]["failure_type"], "FixtureFailure")
        self.assertIsNone(packet["cases"][0]["answer"])

    def test_completed_reviews_bind_exact_original_ids_and_digests(self):
        packet, mapping, reviews = make_review_packet(self.records)
        for review in reviews:
            review.update(
                reviewer="synthetic fixture",
                reviewer_type="assistant",
                blind=False,
                ratings=dict.fromkeys(DIMENSIONS, 0),
                rationale="Fixture negative ratings.",
            )
        bound = bind_packet_reviews(self.records, packet, mapping, reviews)
        self.assertEqual({r["answer_id"] for r in bound}, {r["answer_id"] for r in self.records})
        self.assertTrue(all(not r["blind"] for r in bound))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            bind_packet_reviews(self.records, packet, mapping, reviews + reviews[:1])

    def test_changed_source_packet_and_mapping_are_rejected(self):
        packet, mapping, reviews = make_review_packet(self.records)
        bad_source = copy.deepcopy(self.records)
        bad_source[0]["report"]["conclusion"] = "Changed fixture"
        with self.assertRaisesRegex(ValueError, "changed"):
            bind_packet_reviews(bad_source, packet, mapping, reviews)
        changed = copy.deepcopy(packet)
        changed["cases"][0]["answer"]["conclusion"] = "Changed fixture"
        with self.assertRaisesRegex(ValueError, "changed"):
            bind_packet_reviews(self.records, changed, mapping, reviews)
        forged = copy.deepcopy(mapping)
        forged["packet_sha256"] = _digest(changed)
        for row in forged["mapping"]:
            case = next(c for c in changed["cases"] if c["review_id"] == row["review_id"])
            row["packet_case_sha256"] = _digest(case)
        with self.assertRaisesRegex(ValueError, "original answer"):
            bind_packet_reviews(self.records, changed, forged, reviews)

    def test_output_is_exclusive_and_mapping_is_separate(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "packet"
            result = write_review_packet(self.records, destination)
            self.assertEqual(result["cases"], 3)
            self.assertEqual(
                json.loads((destination / "private-mapping.json").read_text())["version"],
                "policy-masked-v1",
            )
            with self.assertRaises(FileExistsError):
                write_review_packet(self.records, destination)
