"""Export actual tools; altered bundles are explicitly test-only counterexamples."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from neurolab.agent import ResearchAgent
from neurolab.ghana import load_ghana
from neurolab.research_context import ResearchConfiguration, ResearchConstraints
from neurolab.store import RunStore
from scripts.export_investigation import export_bundle, validate_bundle


class InvestigationExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = RunStore(":memory:")
        result = ResearchAgent(
            load_ghana(),
            cls.store,
            configuration=ResearchConfiguration(
                desired_outputs=["ghana_drought_investigation"],
                constraints=ResearchConstraints(max_steps=6, max_tool_calls=6, max_seconds=180),
            ),
            max_steps=6,
            max_tool_calls=6,
            max_wall_time=180,
        ).run("Export the exploratory Ghana investigation without Meta.")
        report = result["report"]
        cls.bundle = {
            "bundle_version": "neurolab-evidence-v1",
            "report": report,
            "artifacts": cls.store.list_artifacts(report["run_id"]),
            "events": cls.store.list_events(report["run_id"]),
        }

    @classmethod
    def tearDownClass(cls):
        cls.store.close()

    def test_portable_figures_use_actual_values_and_preserve_full_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = copy.deepcopy(self.bundle)
            # Untrusted objectives must remain inert in the exported HTML.
            bundle["report"]["objective"] = '<script>alert("untrusted")</script>'
            bundle["report"]["scientific_report"]["objective"] = bundle["report"]["objective"]
            bundle["development_audit"] = {
                "scope": "Engineering fixture, not scientific evidence",
                "note": "<script data-audit-fixture>unsafe()</script>",
            }
            source = root / "bundle.json"
            source.write_text(json.dumps(bundle))
            output = root / "export"
            result = export_bundle(source, output)
            self.assertEqual(result["figure_count"], 4)
            document = (output / "report.html").read_text()
            self.assertNotIn("<script>alert(", document)
            self.assertIn("&lt;script&gt;", document)
            self.assertEqual(document.count('src="data:image/png;base64,'), 4)
            self.assertIn("10. Reproducibility", document)
            self.assertIn("11. Development and verification history", document)
            self.assertIn("Engineering fixture, not scientific evidence", document)
            self.assertNotIn("<script data-audit-fixture>", document)
            self.assertIn("proposal, not executed", document)
            self.assertIn(bundle["report"]["source_sha256"], document)
            self.assertEqual((output / "evidence.json").read_bytes(), source.read_bytes())
            plotted = json.loads((output / "figure-data.json").read_text())
            self.assertAlmostEqual(
                plotted["regime_comparison"]["results"]["mean_yield_by_regime"]["DROUGHT"],
                1230.2687815072015,
            )
            self.assertEqual(len(plotted["trait_correlations"]), 7)
            self.assertEqual(len(plotted["environment_profiles"]["genotypes"]), 5)
            self.assertEqual(len(list(output.glob("*.svg"))), 4)
            for image in output.glob("*.png"):
                self.assertGreater(image.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                export_bundle(source, output)

    def test_incomplete_duplicate_mismatched_and_unrecorded_evidence_is_rejected(self):
        def changed(callback):
            bundle = copy.deepcopy(self.bundle)
            callback(bundle)
            return bundle

        cases = [
            changed(lambda b: b.update(bundle_version="unknown")),
            changed(lambda b: b["report"].update(completion_status="partial")),
            changed(lambda b: b["artifacts"].pop()),
            changed(lambda b: b["artifacts"].__setitem__(0, b["artifacts"][1])),
            changed(lambda b: b["report"].update(evidence_ids=["unowned-id"])),
            changed(lambda b: b["artifacts"][0].update(source_sha256="0" * 64)),
            changed(lambda b: b["events"][0].update(run_id="another-run")),
            changed(lambda b: b.update(events=[])),
            changed(
                lambda b: b["report"]["scientific_report"]["candidate_summaries"][0].update(
                    drought_mean_kg_ha=999999
                )
            ),
        ]
        for bundle in cases:
            with self.subTest(case=cases.index(bundle)), self.assertRaises(ValueError):
                validate_bundle(bundle)
