import csv
import unittest
from pathlib import Path

from scripts.audit_datasets import audit
from scripts.prepare_data import prepare

ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def test_manifest(self):
        self.assertEqual(audit(), 0)

    def test_ghana(self):
        counts = {}
        for name in [
            "maize_drought_phenotypes.csv",
            "maize_wellwatered_phenotypes.csv",
            "maize_combined_phenotypes.csv",
        ]:
            with (ROOT / "data/raw/ghana" / name).open(newline="", encoding="utf-8-sig") as f:
                counts[name] = sum(1 for _ in csv.DictReader(f))
        self.assertEqual(sorted(counts.values()), [432, 432, 864])

    def test_irrigation_clean(self):
        prepare()
        with (ROOT / "data/processed/iita_full_irrigation_clean.csv").open(newline="") as f:
            r = csv.DictReader(f)
            self.assertIn("unnamed_column_3", r.fieldnames)
            self.assertEqual(sum(1 for _ in r), 960)


if __name__ == "__main__":
    unittest.main()
