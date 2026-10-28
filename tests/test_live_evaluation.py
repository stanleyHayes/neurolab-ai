"""Programmed transport and real SQL/numeric tools; no live Meta quality evidence."""

import copy
import hashlib
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

from neurolab.evaluation import TASKS
from neurolab.ghana import load_ghana
from neurolab.live_evaluation import (
    POLICIES,
    SEEDS,
    RecordedAdapter,
    collect_live_matrix,
    execute_live_trial,
    trial_configuration,
    trial_matrix,
    validate_live_protocol,
)
from neurolab.model_spend import SpendPolicy
from neurolab.providers import ModelProviderError
from neurolab.store import RunStore
from tests.test_providers import SPEND_ENV

ROOT = Path(__file__).resolve().parents[1]


class LiveCollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def setUp(self):
        env = patch.dict(
            os.environ,
            {
                **SPEND_ENV,
                "META_MODEL_API_KEY": "fixture-private-key",
                "META_MODEL_VERIFIED": "true",
                "MODEL_INFERENCE_ENABLED": "true",
                "MODEL_MAX_OUTPUT_TOKENS": "100",
                "MODEL_MAX_RUN_TOKENS": "100000",
            },
        )
        env.start()
        self.addCleanup(env.stop)
        self.store = RunStore(":memory:")
        self.addCleanup(self.store.close)
        self.owner = self.store.create_user("collector@example.test", "fixture", "Collector")[
            "user_id"
        ]
        policy = SpendPolicy.from_environment()
        paths = [
            *ROOT.glob("neurolab/*.py"),
            ROOT / "requirements.txt",
            ROOT / "scripts/collect_live_evaluation.py",
            ROOT / "schemas/agent_tool_call.schema.json",
            ROOT / "eval/tasks.json",
            ROOT / "data/raw/ghana/maize_combined_phenotypes.csv",
        ]
        self.manifest = {
            "protocol_id": "synthetic-harness-test-only",
            "status": "APPROVED FOR COLLECTION",
            "policies": list(POLICIES),
            "seeds": list(SEEDS),
            "accuracy_tasks": [t["task_id"] for t in TASKS],
            "utility_tasks": [t["task_id"] for t in TASKS[:10]],
            "planned_research_trials": 180,
            "planned_meta_trials": 72,
            "per_trial_maxima": {"numeric_calls": 2, "steps": 2, "wall_seconds": 60},
            "input_sha256": {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
            },
            "spend_policy_sha256": policy.digest,
            "model_id": "fixture",
            "provider_account_controls_verified": True,
            "owner_authorized": True,
            "approved_utc_day": datetime.now(UTC).date().isoformat(),
            "approved_spend_cap_micro_usd": policy.global_day_micro_usd,
            "max_output_tokens": 100,
        }

    def test_exact_matrix_and_identical_paired_initial_configuration(self):
        trials = trial_matrix()
        self.assertEqual(len(trials), 180)
        self.assertEqual(sum(t["policy"].startswith("meta_") for t in trials), 72)
        self.assertEqual(len({(t["task"]["task_id"], t["seed"], t["policy"]) for t in trials}), 180)
        self.assertEqual(trial_configuration(trials[0]), trial_configuration(trials[1]))
        for trial in trials:
            self.assertEqual(trial_configuration(trial).constraints.max_steps, 2)
            original = trial_configuration(trial)
            from_independent_input = trial_configuration(copy.deepcopy(trial))
            self.assertEqual(original, from_independent_input)

    def test_preflight_rejects_old_manifest_stale_source_inactive_owner_and_budget(self):
        validate_live_protocol(self.manifest, self.dataset, self.store, self.owner, ROOT)
        for field, value in (
            ("status", "FROZEN PLAN ONLY"),
            ("owner_authorized", False),
            ("approved_spend_cap_micro_usd", 0),
            ("model_id", "different"),
            ("provider_account_controls_verified", False),
            ("approved_utc_day", "2000-01-01"),
        ):
            manifest = {**self.manifest, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_live_protocol(manifest, self.dataset, self.store, self.owner, ROOT)
        changed = copy.deepcopy(self.manifest)
        changed["input_sha256"]["neurolab/agent.py"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "changed"):
            validate_live_protocol(changed, self.dataset, self.store, self.owner, ROOT)
        with self.assertRaisesRegex(ValueError, "active"):
            validate_live_protocol(self.manifest, self.dataset, self.store, "unknown", ROOT)

    def test_refusals_remain_in_full_denominator_and_output_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "collection"
            runner = Mock(side_effect=ValueError("fixture-private-key must not be logged"))
            summary = collect_live_matrix(
                self.manifest,
                self.dataset,
                self.store,
                self.owner,
                destination,
                ROOT,
                runner=runner,
            )
            self.assertEqual(summary["records"], 180)
            self.assertEqual(runner.call_count, 180)
            text = (destination / "results.jsonl").read_text()
            records = [json.loads(row) for row in text.splitlines()]
            self.assertTrue(all(r["failure_type"] == "ValueError" for r in records))
            self.assertNotIn("fixture-private-key", text)
            with self.assertRaises(FileExistsError):
                collect_live_matrix(
                    self.manifest,
                    self.dataset,
                    self.store,
                    self.owner,
                    destination,
                    ROOT,
                    runner=runner,
                )
            self.assertEqual(runner.call_count, 180)

    def test_interruption_flushes_attempt_and_result_without_retry(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "interrupted"
            runner = Mock(side_effect=KeyboardInterrupt())
            with self.assertRaises(KeyboardInterrupt):
                collect_live_matrix(
                    self.manifest,
                    self.dataset,
                    self.store,
                    self.owner,
                    destination,
                    ROOT,
                    runner=runner,
                )
            records = (destination / "results.jsonl").read_text().splitlines()
            self.assertEqual(len(records), 1)
            self.assertTrue(json.loads(records[0])["interrupted"])
            self.assertEqual(len((destination / "attempts.jsonl").read_text().splitlines()), 1)
            self.assertEqual(runner.call_count, 1)

    def test_paired_actual_adapter_preserves_owner_spend_and_only_withholds_evidence(self):
        responses = []
        for action in ("dataset_profile", "inspect_missingness") * 2:
            reply = {
                "choice": {"action": action, "bootstrap_samples": None},
                "decision_summary": "Fixture selection, not live model reasoning.",
            }
            response = Mock(status=200)
            response.read.return_value = json.dumps(
                {
                    "choices": [
                        {"message": {"content": json.dumps(reply)}, "finish_reason": "stop"}
                    ],
                    "usage": {"total_tokens": 10},
                }
            ).encode()
            responses.append(response)
        connection = Mock()
        connection.getresponse.side_effect = responses
        with (
            tempfile.TemporaryDirectory() as root,
            patch("neurolab.providers.http.client.HTTPSConnection", return_value=connection),
        ):
            path = Path(root) / "provider.jsonl"
            outcomes = [
                execute_live_trial(
                    {**trial, "approved_utc_day": self.manifest["approved_utc_day"]},
                    self.dataset,
                    self.store,
                    self.owner,
                    path,
                )
                for trial in trial_matrix()[:2]
            ]
            transcript = [json.loads(row) for row in path.read_text().splitlines()]
            self.assertNotIn("fixture-private-key", path.read_text())
        requests = [row["body"] for row in transcript if row["kind"] == "provider.request"]
        self.assertEqual(len(requests), 4)
        self.assertEqual(requests[0], requests[2])
        self.assertTrue(json.loads(requests[1]["messages"][1]["content"])["evidence"])
        self.assertEqual(json.loads(requests[3]["messages"][1]["content"])["evidence"], [])
        for result in outcomes:
            self.assertEqual(result["model_calls"], 2)
            self.assertEqual(len(result["spend_reservations"]), 2)
            self.assertEqual(len(result["artifacts"]), 2)
            self.assertEqual(self.store.get_run(result["run_id"])["owner_user_id"], self.owner)

    def test_trial_failure_preserves_owned_run_and_blocks_false_offline_scoring(self):
        from neurolab.answer_evaluation import summarize_answers

        trial = {**trial_matrix()[2], "approved_utc_day": self.manifest["approved_utc_day"]}
        with (
            tempfile.TemporaryDirectory() as root,
            patch(
                "neurolab.live_evaluation.ResearchAgent.run",
                side_effect=RuntimeError("private fixture"),
            ),
        ):
            result = execute_live_trial(
                trial, self.dataset, self.store, self.owner, Path(root) / "transcript.jsonl"
            )
        self.assertEqual(result["failure_type"], "RuntimeError")
        self.assertIsNone(result["report"])
        self.assertEqual(self.store.get_run(result["run_id"])["status"], "FAILED")
        self.assertEqual(result["model_calls"], 0)
        self.assertTrue(result["events"])
        with self.assertRaisesRegex(ValueError, "seed-aware"):
            summarize_answers([{**trial, **result}])

    def test_daily_expiry_stops_transport(self):
        adapter = RecordedAdapter.from_environment()
        adapter.approved_utc_day = "2000-01-01"
        with patch("neurolab.providers.http.client.HTTPSConnection") as network:
            with self.assertRaisesRegex(ModelProviderError, "expired"):
                adapter._send_structured(None, {}, 1)
            network.assert_not_called()
