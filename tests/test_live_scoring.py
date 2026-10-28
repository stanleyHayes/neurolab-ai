"""Synthetic rating/empty-answer fixtures only; never live model-quality evidence."""

import copy
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from neurolab.answer_evaluation import DIMENSIONS, answer_digest, review_template
from neurolab.evaluation import TASKS
from neurolab.live_evaluation import POLICIES, trial_matrix
from neurolab.live_scoring import _exact_question_interval, summarize_live_answers
from scripts.score_live_evaluation import main


def fixture_records():
    records = []
    for trial in trial_matrix():
        task, seed, policy = trial["task"], trial["seed"], trial["policy"]
        record = {
            **trial,
            "answer_id": f"{policy}/{seed}/{task['task_id']}",
            "budget": 2,
            "report": {
                "objective": task["objective"],
                "seed": seed,
                "tool_calls": 0,
                "run_id": f"fixture-{policy}-{seed}-{task['task_id']}",
                "source_sha256": "fixture-source-only",
                "evidence_ids": [],
                "grounded_claims": [],
                "conclusion": "Synthetic scoring fixture; no scientific finding.",
            },
            "artifacts": [],
            "events": [],
            "wall_seconds": 0.1,
            "model_calls": 0,
            "spend_reservations": [],
        }
        record["answer_sha256"] = answer_digest(record)
        records.append(record)
    return records


def fixture_reviews(records, rating=1):
    reviews = review_template(records)
    for review in reviews:
        review.update(
            reviewer="Synthetic assistant fixture",
            reviewer_type="assistant",
            blind=False,
            ratings=dict.fromkeys(DIMENSIONS, rating),
            rationale="Fixture scoring only.",
        )
    return reviews


class LiveScoringTests(unittest.TestCase):
    def test_exact_bootstrap_matches_hand_counted_distributions(self):
        # Four equally likely values: sum multiplicities are
        # 1,4,10,20,31,40,44,40,31,20,10,4,1 out of256 sequences.
        interval = _exact_question_interval(
            [Fraction(0), Fraction(1, 3), Fraction(2, 3), Fraction(1)]
        )
        self.assertEqual(interval, [1 / 6, 5 / 6])
        # Empirical Bernoulli(1/4), four draws: upper2.5% cutoff is3/4.
        repeated = _exact_question_interval([Fraction(0), Fraction(0), Fraction(0), Fraction(1)])
        self.assertEqual(repeated, [0, 0.75])

    def test_complete_matrix_keeps_seeds_inside_question_and_fixed_subsets(self):
        records = fixture_records()
        reviews = fixture_reviews(records)
        for record, review in zip(records, reviews, strict=True):
            review["ratings"] = dict.fromkeys(DIMENSIONS, int(record["task"] == TASKS[0]))
        summary = summarize_live_answers(records, reviews)
        self.assertTrue(summary["collection_complete"])
        self.assertFalse(summary["independence_verified"])
        self.assertIsNone(summary["winner"])
        for policy in POLICIES:
            scores = summary["policies"][policy]
            accuracy = scores["accuracy_all_12"]["answers_question"]
            utility = scores["utility_first_10"]["answers_question"]
            self.assertAlmostEqual(accuracy["question_macro_mean"], 1 / 12)
            self.assertEqual(accuracy["expected_questions"], 12)
            self.assertEqual(utility["expected_questions"], 10)
            self.assertAlmostEqual(utility["question_macro_mean"], 0.1)
            self.assertEqual(
                scores["questions"][0]["dimensions"]["answers_question"]["scored_trials"], 3
            )
            low, high = accuracy["question_bootstrap_95_interval"]
            self.assertLessEqual(low, 1 / 12)
            self.assertGreaterEqual(high, 1 / 12)

    def test_seed_variation_is_not_resampled_as_independent_questions(self):
        records = fixture_records()
        reviews = fixture_reviews(records)
        for record, review in zip(records, reviews, strict=True):
            review["ratings"] = dict.fromkeys(DIMENSIONS, int(record["seed"] == 2026))
        summary = summarize_live_answers(records, reviews)
        for result in summary["policies"].values():
            score = result["accuracy_all_12"]["answers_question"]
            self.assertAlmostEqual(score["question_macro_mean"], 1 / 3)
            for bound in score["question_bootstrap_95_interval"]:
                self.assertAlmostEqual(bound, 1 / 3)
            seed_results = result["questions"][0]["dimensions"]["answers_question"]["seed_results"]
            self.assertEqual([row["value"] for row in seed_results], [1, 0, 0])

    def test_reportless_failures_zero_direct_usefulness_but_exclude_claim_scope(self):
        records = fixture_records()
        for row in records:
            row["report"] = None
            row["failure_type"] = "FixtureFailure"
            row["answer_sha256"] = answer_digest(row)
        summary = summarize_live_answers(records)
        self.assertEqual(summary["reviews_completed"], 0)
        for result in summary["policies"].values():
            direct = result["accuracy_all_12"]["answers_question"]
            supported = result["accuracy_all_12"]["claims_supported"]
            self.assertEqual(direct["question_macro_mean"], 0)
            self.assertEqual(direct["automatic_no_answer_zeros"], 36)
            self.assertEqual(direct["question_bootstrap_95_interval"], [0, 0])
            self.assertIsNone(supported["question_macro_mean"])
            self.assertEqual(supported["reportless_excluded_trials"], 36)
            self.assertEqual(supported["eligible_questions"], 0)
        positive_missing_answer_reviews = fixture_reviews(records)
        with self.assertRaisesRegex(ValueError, "missing answer"):
            summarize_live_answers(records, positive_missing_answer_reviews)

    def test_failed_question_stays_in_direct_but_not_output_only_denominator(self):
        records = fixture_records()
        for row in records:
            if row["task"] == TASKS[0]:
                row["report"] = None
                row["answer_sha256"] = answer_digest(row)
        reviews = fixture_reviews([row for row in records if row["report"] is not None])
        summary = summarize_live_answers(records, reviews)
        for result in summary["policies"].values():
            direct = result["accuracy_all_12"]["answers_question"]
            output_only = result["accuracy_all_12"]["claims_supported"]
            self.assertAlmostEqual(direct["question_macro_mean"], 11 / 12)
            self.assertEqual(direct["eligible_questions"], 12)
            self.assertEqual(output_only["question_macro_mean"], 1)
            self.assertEqual(output_only["eligible_questions"], 11)
            self.assertEqual(output_only["reportless_excluded_trials"], 3)

    def test_unreviewed_outputs_and_unattempted_cells_remain_unknown(self):
        records = fixture_records()
        summary = summarize_live_answers(records)
        self.assertEqual(summary["report_outputs_unreviewed"], 180)
        self.assertIsNone(
            summary["policies"][POLICIES[0]]["accuracy_all_12"]["answers_question"][
                "question_macro_mean"
            ]
        )
        removed = records.pop()
        summary = summarize_live_answers(records, fixture_reviews(records))
        self.assertFalse(summary["collection_complete"])
        result = summary["policies"][removed["policy"]]["accuracy_all_12"]["answers_question"]
        self.assertEqual(result["missing_trials"], 1)
        self.assertIsNone(result["question_macro_mean"])
        self.assertEqual(result["scored_questions"], 11)

    def test_observed_calls_unknown_reservations_and_invoice_are_distinct(self):
        records = fixture_records()
        records[0].update(
            model_calls=2, spend_reservations=[{"reserved_micro_usd": 123, "outcome": "unknown"}]
        )
        summary = summarize_live_answers(records)
        totals = summary["policies"][POLICIES[0]]["operational_totals"]
        self.assertEqual(totals["model_calls"], 2)
        self.assertEqual(totals["reserved_micro_usd"], 123)
        self.assertIsNone(totals["invoice_cost_usd"])
        del records[0]["model_calls"]
        del records[0]["spend_reservations"]
        summary = summarize_live_answers(records)
        totals = summary["policies"][POLICIES[0]]["operational_totals"]
        self.assertIsNone(totals["model_calls"])
        self.assertIsNone(totals["reserved_micro_usd"])
        self.assertEqual(totals["unknown_call_count_records"], 1)

    def test_duplicate_unknown_changed_records_and_bad_metadata_rejected(self):
        records = fixture_records()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summarize_live_answers(records + records[:1])
        changed = copy.deepcopy(records)
        changed[0]["report"]["conclusion"] = "Changed"
        with self.assertRaisesRegex(ValueError, "changed"):
            summarize_live_answers(changed)
        for field, value in (("seed", 1), ("model_calls", -1), ("wall_seconds", float("inf"))):
            changed = copy.deepcopy(records)
            changed[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                summarize_live_answers(changed)
        reviews = fixture_reviews(records)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize_live_answers(records, reviews + reviews[:1])

    def test_cli_never_overwrites_existing_summary(self):
        records = fixture_records()[:1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, reviews, output = (
                root / "records.jsonl",
                root / "reviews.json",
                root / "out.json",
            )
            source.write_text(json.dumps(records[0]) + "\n")
            reviews.write_text("[]")
            output.write_text("preserve")
            with (
                patch(
                    "sys.argv",
                    [
                        "score_live_evaluation",
                        "--records",
                        str(source),
                        "--reviews",
                        str(reviews),
                        "--output",
                        str(output),
                    ],
                ),
                self.assertRaises(FileExistsError),
            ):
                main()
            self.assertEqual(output.read_text(), "preserve")
