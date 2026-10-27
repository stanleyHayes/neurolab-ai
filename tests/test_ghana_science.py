import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.ghana import load_ghana, write_normalized  # noqa: E402
from neurolab.science import (  # noqa: E402
    compare_regimes,
    dataset_profile,
    inspect_missingness,
    rank_genotypes,
)


class GhanaNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def test_lineage_and_source_contract(self):
        dataset = self.dataset
        self.assertEqual(dataset.source_row_count, 864)
        self.assertEqual(dataset.yield_unit, "kg/ha")
        self.assertEqual(len({row["source_row_number"] for row in dataset.records}), 864)
        self.assertEqual(len({row["source_sha256"] for row in dataset.records}), 1)
        self.assertEqual(dataset.records[0]["source_row_number"], 2)
        self.assertEqual(dataset.records[0]["year_code"], "1")
        self.assertEqual(dataset.records[0]["environment_code"], "DROUGHT_Y1")
        self.assertIsNone(dataset.records[0]["location_code"])

    def test_missingness_and_raw_columns_retained(self):
        profile = dataset_profile(self.dataset)
        self.assertEqual(profile["genotype_count"], 72)
        self.assertEqual(profile["water_regimes"], {"DROUGHT": 432, "WELL_WATERED": 432})
        self.assertEqual(profile["missingness"]["stay_green_score"], {"missing": 432, "total": 864})
        extra = json.loads(self.dataset.records[0]["raw_extra_json"])
        self.assertIn("PASP", extra)
        self.assertIn("EASP", extra)
        self.assertNotIn("GENO", extra)  # GENO is absent from the combined source schema.

    def test_write_and_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "normalized.csv"
            quarantine = Path(tmp) / "quarantine.csv"
            write_normalized(self.dataset, out, quarantine)
            with out.open(encoding="utf-8", newline="") as stream:
                normalized = list(csv.DictReader(stream))
            with quarantine.open(encoding="utf-8", newline="") as stream:
                quarantined = list(csv.DictReader(stream))
            self.assertEqual(len(normalized), 864)
            self.assertEqual(quarantined, [])

    def test_bad_numeric_row_is_not_dropped_and_is_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            (temp_root / "data/raw/ghana").mkdir(parents=True)
            source = (ROOT / "data/raw/ghana/maize_combined_phenotypes.csv").read_text()
            lines = source.splitlines()
            columns = lines[0].split(",")
            yield_index = columns.index("YIELD")
            fields = lines[1].split(",")
            fields[yield_index] = "not-a-number"
            lines[1] = ",".join(fields)
            (temp_root / "data/raw/ghana/maize_combined_phenotypes.csv").write_text(
                "\n".join(lines) + "\n"
            )
            (temp_root / "data/raw/ghana/data_dictionary.csv").write_bytes(
                (ROOT / "data/raw/ghana/data_dictionary.csv").read_bytes()
            )
            dataset = load_ghana(temp_root)
            self.assertEqual(dataset.source_row_count, 864)
            self.assertIsNone(dataset.records[0]["grain_yield_value"])
            self.assertEqual(len(dataset.quarantine_rows), 1)
            self.assertIn("not-a-number", dataset.quarantine_rows[0]["raw_source_json"])


class GhanaScienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def test_regime_contrast_is_reproducible_and_caveated(self):
        first = compare_regimes(self.dataset, seed=17, bootstrap_samples=200)
        second = compare_regimes(self.dataset, seed=17, bootstrap_samples=200)
        self.assertEqual(first, second)
        self.assertEqual(first["claim_scope"], "exploratory")
        self.assertEqual(first["sample_size"], 864)
        self.assertEqual(
            first["results"]["plot_count_by_regime"], {"DROUGHT": 432, "WELL_WATERED": 432}
        )
        self.assertEqual(len(first["uncertainty"]["yield_difference_95_ci_kg_ha"]), 2)
        self.assertIn("not a causal", " ".join(first["warnings"]))

    def test_rank_and_missingness_outputs_have_provenance(self):
        ranked = rank_genotypes(self.dataset)
        missing = inspect_missingness(self.dataset)
        self.assertEqual(ranked["sample_size"], 432)
        self.assertEqual(len(ranked["results"]["genotypes"]), 72)
        self.assertEqual(missing["source_sha256"], self.dataset.source_sha256)
        self.assertEqual(missing["results"]["missingness"]["stay_green_score"]["missing"], 432)

    def test_bootstrap_budget_validation(self):
        with self.assertRaises(ValueError):
            compare_regimes(self.dataset, bootstrap_samples=99)


if __name__ == "__main__":
    unittest.main()
