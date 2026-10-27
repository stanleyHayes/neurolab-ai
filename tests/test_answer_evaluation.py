"""Actual local answers and explicitly altered audit/review counterexamples."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from neurolab.answer_evaluation import (
    ALLOWED,
    DIMENSIONS,
    POLICIES,
    _wilson,
    answer_digest,
    audit_trace,
    collect_answers,
    review_template,
    summarize_answers,
    write_answer_evaluation,
)
from neurolab.evaluation import TASKS
from neurolab.ghana import load_ghana


class AnswerEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana()
        cls.records = collect_answers(cls.dataset, tasks=TASKS[:1], budget=2)

    def test_real_answers_share_budget_data_and_disclose_actual_replay(self):
        self.assertEqual(len(TASKS), 12)
        self.assertEqual(len(ALLOWED), 6)
        self.assertIn("analyze_trait_associations", ALLOWED)
        self.assertIn("summarize_environment_stability", ALLOWED)
        self.assertEqual({r["policy"] for r in self.records}, set(POLICIES))
        for record in self.records:
            self.assertIsNotNone(record["report"], record.get("failure_type"))
            self.assertLessEqual(record["report"]["tool_calls"], 2)
            self.assertEqual(record["report"]["source_sha256"], self.dataset.source_sha256)
            self.assertEqual(record["report"]["mode"], "deterministic_replay")
            self.assertEqual(record["model_calls"], 0)
            self.assertEqual(record["eligible_tools"], list(ALLOWED))
            self.assertEqual(record["answer_sha256"], answer_digest(record))
            audit = record["trace_audit"]
            self.assertEqual(audit["schema_valid_calls"], audit["requested_calls"])
            self.assertEqual(audit["claims_with_existing_citations"], audit["claim_count"])
            self.assertTrue(audit["source_consistent"])
        with self.assertRaises(ValueError):
            collect_answers(self.dataset, budget=3)

    def test_missing_reviews_are_null_not_perfect_or_zero_accuracy(self):
        summary = summarize_answers(self.records, review_template(self.records))
        self.assertEqual(summary["semantic_reviews_completed"], 0)
        self.assertEqual(summary["semantic_reviews_pending"], 3)
        self.assertIn("NOT RUN", summary["model_comparison"])
        for metrics in summary["policies"].values():
            self.assertEqual(metrics["trace_metrics"]["schema_valid_fraction"], 1)
            self.assertEqual(metrics["trace_metrics"]["citation_exists_fraction"], 1)
        for policy in summary["policies"].values():
            for score in policy["semantic_ratings"].values():
                self.assertIsNone(score["fraction"])
                self.assertIsNone(score["wilson_95_interval"])

    def test_evidence_bound_ratings_and_intervals_preserve_negative_judgments(self):
        reviews = review_template(self.records)
        for review in reviews:
            review.update(
                reviewer="unit-test assistant",
                reviewer_type="assistant",
                blind=False,
                rationale="Test-only rubric exercise; not a real semantic adjudication.",
                ratings=dict.fromkeys(DIMENSIONS, 0),
            )
        summary = summarize_answers(self.records, reviews)
        self.assertEqual(summary["semantic_reviews_completed"], 3)
        for policy in summary["policies"].values():
            self.assertEqual(policy["semantic_ratings"]["answers_question"]["fraction"], 0)
            self.assertFalse(policy["all_reviews_blind"])
            self.assertEqual(policy["reviewer_types"], ["assistant"])
        low, high = _wilson(1, 2)
        self.assertAlmostEqual(low, 0.0945312, places=6)
        self.assertAlmostEqual(high, 0.9054688, places=6)
        self.assertIsNone(_wilson(0, 0))

    def test_stale_unknown_duplicate_and_invalid_reviews_cannot_be_scored(self):
        template = review_template(self.records)[0]
        valid = {
            **template,
            "reviewer": "test",
            "reviewer_type": "human",
            "blind": True,
            "rationale": "Test-only adjudication.",
            "ratings": dict.fromkeys(DIMENSIONS, 1),
        }
        cases = [
            [{**valid, "answer_id": "unknown"}],
            [valid, valid],
            [template, template],
            [{**valid, "answer_sha256": "stale"}],
            [{**valid, "ratings": {"answers_question": 1}}],
            [{**valid, "ratings": dict.fromkeys(DIMENSIONS, True)}],
            [{**valid, "reviewer_type": "fabricated-human"}],
            [{**valid, "rationale": ""}],
        ]
        for reviews in cases:
            with self.subTest(reviews=reviews), self.assertRaises(ValueError):
                summarize_answers(self.records, reviews)
        changed = copy.deepcopy(self.records)
        changed[0]["report"]["conclusion"] += " changed answer"
        with self.assertRaises(ValueError):
            summarize_answers(changed, [valid])
        with self.assertRaises(ValueError):
            summarize_answers(changed)
        with self.assertRaises(ValueError):
            summarize_answers(self.records + [self.records[0]])

    def test_trace_audit_detects_bad_citations_actions_hashes_but_does_not_score_prose(self):
        record = copy.deepcopy(self.records[0])
        report, artifacts, events = record["report"], record["artifacts"], record["events"]
        # This intentionally false sentence demonstrates why trace validity is not entailment.
        report["grounded_claims"][0]["claim"] = "Invented yield: 999999 kg/ha."
        report["conclusion"] = "Invented yield: 999999 kg/ha."
        audit = audit_trace(report, artifacts, events)
        self.assertEqual(audit["claims_with_existing_citations"], audit["claim_count"])
        self.assertIn("no factual entailment", audit["scope"])
        report["grounded_claims"][0]["evidence_ids"] = ["missing"]
        artifacts[0]["source_sha256"] = "0" * 64
        event = next(e for e in events if e["event_type"] == "tool.requested")
        event["payload"]["action"] = "run_shell"
        audit = audit_trace(report, artifacts, events)
        self.assertLess(audit["claims_with_existing_citations"], audit["claim_count"])
        self.assertLess(audit["schema_valid_calls"], audit["requested_calls"])
        self.assertFalse(audit["source_consistent"])
        self.assertFalse(audit_trace(report, [], events)["report_evidence_ids_match"])

    def test_all_unexpected_failures_are_recorded_and_partial_trace_is_retained(self):
        def fail(agent, _objective, *, run_id, seed):
            agent.store.add_event(run_id, "test.failure", {"summary": "Explicit test-only failure"})
            raise RuntimeError("Do not expose this private exception text")

        with patch("neurolab.answer_evaluation.ResearchAgent.run", fail):
            records = collect_answers(self.dataset, tasks=TASKS[:1])
        self.assertEqual(len(records), 3)
        self.assertTrue(all(r["failure_type"] == "RuntimeError" for r in records))
        self.assertTrue(all(r["events"][-1]["event_type"] == "test.failure" for r in records))
        self.assertNotIn("private exception text", json.dumps(records))
        summary = summarize_answers(records)
        self.assertTrue(all(p["execution_failures"] == 1 for p in summary["policies"].values()))

    def test_output_preserves_jsonl_and_requires_a_new_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evaluation"
            with patch("neurolab.answer_evaluation.collect_answers", return_value=self.records):
                summary = write_answer_evaluation(self.dataset, output)
            loaded = [
                json.loads(line) for line in (output / "results.jsonl").read_text().splitlines()
            ]
            self.assertEqual(loaded, self.records)
            self.assertEqual(summary["record_count"], 3)
            self.assertEqual(len(json.loads((output / "tasks.json").read_text())), 12)
            with self.assertRaises(FileExistsError):
                write_answer_evaluation(self.dataset, output)
