"""Explicit synthetic controls, not a live Meta injection benchmark."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from neurolab.adversarial_evaluation import CASES, collect_probes
from neurolab.agent import ResearchAgent
from neurolab.research_context import ResearchRunRequest
from scripts.evaluate_adversarial_contracts import main


class AdversarialContractTests(unittest.TestCase):
    def test_csv_labels_reach_model_input_and_unsafe_replies_are_contained(self):
        with patch("neurolab.providers.http.client.HTTPSConnection") as network:
            result = collect_probes()
        network.assert_not_called()
        self.assertTrue(result["all_contract_checks_passed"])
        self.assertTrue(result["canonical_sources_unchanged"])
        self.assertEqual(len(result["records"]), 10)
        cases = json.loads(CASES.read_text())
        for case in cases:
            pair = [record for record in result["records"] if record["case_id"] == case["case_id"]]
            self.assertEqual(len(pair), 2)
            self.assertEqual(pair[0]["fixture_source_sha256"], pair[1]["fixture_source_sha256"])
            self.assertEqual(pair[0]["request_schemas"], pair[1]["request_schemas"])
            self.assertEqual(pair[0]["fixture_messages"][0], pair[1]["fixture_messages"][0])
            for record in pair:
                self.assertEqual(record["live_model_calls"], 0)
                self.assertEqual(record["fixture_adapter_calls"], 2)
                self.assertTrue(all(record["contract_checks"].values()))
                self.assertIn("synthetic", record["scope"])

    def test_unexercised_or_failed_trials_do_not_become_successes(self):
        with patch(
            "neurolab.adversarial_evaluation._fixture",
            side_effect=ValueError("Synthetic fixture failure"),
        ):
            result = collect_probes()
        self.assertFalse(result["all_contract_checks_passed"])
        self.assertEqual(len(result["records"]), 10)
        self.assertTrue(all(record["failure_type"] == "ValueError" for record in result["records"]))
        self.assertTrue(result["canonical_sources_unchanged"])

    def test_feedback_control_is_internal_and_does_not_silence_replay_evidence(self):
        for settings in ({"model_feedback": "false"}, {"model_feedback": False, "mode": "replay"}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                ResearchAgent(None, None, **settings)
        with self.assertRaises(ValidationError):
            ResearchRunRequest(objective="Question", model_feedback=False)

    def test_cli_preserves_existing_evaluation_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text("preserve earlier failed trial")
            with (
                patch("sys.argv", ["evaluate_adversarial_contracts", "--output", str(path)]),
                self.assertRaises(FileExistsError),
            ):
                main()
            self.assertEqual(path.read_text(), "preserve earlier failed trial")
