import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.evaluation import evaluate_baselines, write_evaluation  # noqa: E402
from neurolab.ghana import load_ghana  # noqa: E402


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def test_baseline_comparison_is_reproducible_and_discloses_model_block(self):
        first = evaluate_baselines(self.dataset, seed=41, budget=2)
        second = evaluate_baselines(self.dataset, seed=41, budget=2)
        self.assertEqual(first, second)
        self.assertIn("not run", first["model_comparison"])
        self.assertEqual(len(first["tasks"]), 12)
        self.assertIn("no language-model answer is scored", first["scope_note"])
        for task in first["tasks"]:
            for baseline in ("fixed_workflow", "seeded_random", "deterministic_replay"):
                self.assertLessEqual(task[baseline]["budget_used"], 2)

    def test_results_written_to_expected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            report = write_evaluation(self.dataset, Path(directory), seed=2)
            self.assertTrue((Path(directory) / "tasks.json").is_file())
            loaded = json.loads((Path(directory) / "results.json").read_text())
            self.assertEqual(loaded["source_sha256"], self.dataset.source_sha256)
            self.assertEqual(report, loaded)

    def test_rejects_unbounded_budget(self):
        with self.assertRaises(ValueError):
            evaluate_baselines(self.dataset, budget=11)


if __name__ == "__main__":
    unittest.main()
