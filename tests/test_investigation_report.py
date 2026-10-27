"""Actual-source acceptance plus explicitly synthetic counterexamples; no inference."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from neurolab.agent import ResearchAgent
from neurolab.ghana import load_ghana
from neurolab.investigation_profile import (
    PROFILE_METHODS,
    PROFILE_OUTPUT,
    profile_followup,
    profile_plan_check,
)
from neurolab.provenance import RUNTIME_PROVENANCE, git_revision
from neurolab.research_context import (
    ResearchConfiguration,
    ResearchConstraints,
    build_deterministic_plan,
)
from neurolab.scientific_report import build_scientific_report
from neurolab.source_inventory import source_inventory
from neurolab.store import RunStore

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE = (ROOT / "tests/fixtures/ghana-research-objective.txt").read_text()


def configuration(**patch):
    return ResearchConfiguration(
        desired_outputs=[PROFILE_OUTPUT],
        constraints=ResearchConstraints(max_steps=6, max_tool_calls=6, max_seconds=180),
        **patch,
    )


class InvestigationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = RunStore(":memory:")
        cls.result = ResearchAgent(
            load_ghana(),
            cls.store,
            configuration=configuration(),
            max_steps=6,
            max_tool_calls=6,
            max_wall_time=180,
        ).run(OBJECTIVE)
        cls.report = cls.result["report"]
        cls.science = cls.report["scientific_report"]
        cls.artifacts = cls.store.list_artifacts(cls.report["run_id"])

    @classmethod
    def tearDownClass(cls):
        cls.store.close()

    def test_exact_supplied_objective_full_six_method_plan_and_preexecution_hypotheses(self):
        self.assertEqual(self.report["objective"], OBJECTIVE)
        self.assertEqual(self.science["objective"], OBJECTIVE)
        self.assertEqual(self.report["completion_status"], "complete")
        self.assertEqual(self.report["tool_calls"], 6)
        self.assertEqual(len(self.report["research_plan"]["analysis_approaches"]), 6)
        events = self.store.list_events(self.report["run_id"])
        first = min(e["sequence"] for e in events if e["event_type"] == "tool.requested")
        hypotheses = [e for e in events if e["event_type"] == "hypothesis.proposed"]
        self.assertEqual(len(hypotheses), 4)
        self.assertTrue(all(e["sequence"] < first for e in hypotheses))
        prepared = next(e for e in events if e["event_type"] == "research.investigation_prepared")
        self.assertLess(prepared["sequence"], first)
        generated = next(event for event in events if event["event_type"] == "report.generated")
        last_tool = max(
            event["sequence"] for event in events if event["event_type"] == "tool.completed"
        )
        self.assertGreater(generated["sequence"], last_tool)
        self.assertEqual(
            set(generated["payload"]["evidence_ids"]), set(self.report["evidence_ids"])
        )
        self.assertEqual(len(prepared["payload"]["hypotheses"]), 4)
        self.assertTrue(
            all(h["criterion"] and h["rationale"] for h in prepared["payload"]["hypotheses"])
        )
        self.assertEqual(self.report["mode"], "deterministic_replay")
        self.assertIsNone(self.report["model_provider"])

    def test_actual_findings_and_contradictions_are_grounded_without_field_validation(self):
        hypotheses = {item["id"]: item for item in self.science["hypothesis_evaluations"]}
        self.assertEqual(hypotheses["H1"]["verdict"], "criterion_met")
        self.assertEqual(len(hypotheses["H1"]["matching_genotype_ids"]), 5)
        self.assertEqual(hypotheses["H2"]["verdict"], "inconclusive")
        self.assertTrue(any("includes zero" in text for text in hypotheses["H2"]["contradictions"]))
        self.assertEqual(hypotheses["H3"]["verdict"], "criterion_met")
        self.assertIn("unverified", hypotheses["H3"]["rationale"])
        self.assertEqual(hypotheses["H4"]["verdict"], "criterion_met")
        ids = {item["artifact_id"] for item in self.artifacts}
        self.assertTrue(
            all(
                set(h["evidence_ids"]).issubset(ids) and h["evidence_ids"]
                for h in hypotheses.values()
            )
        )
        self.assertEqual(self.science["conclusion_status"], "exploratory_not_field_validated")
        candidates = self.science["candidate_summaries"]
        self.assertEqual(candidates[0]["genotype_id"], "TZm-1179")
        self.assertAlmostEqual(
            candidates[0]["observed_regime_summary"]["descriptive_retention_percent"], 64.7170942954
        )
        self.assertTrue(
            any(
                item["observed_regime_summary"]["descriptive_retention_percent"] > 100
                for item in candidates
            )
        )
        self.assertEqual(self.science["next_experiment"]["status"], "proposal_only_not_executed")
        self.assertIn("Not calculated", self.science["next_experiment"]["sample_size"])
        json.dumps(self.science, allow_nan=False)

    def test_followup_choices_depend_on_actual_evidence_and_are_executed(self):
        decisions = [
            d
            for d in self.report["decisions"]
            if d["selection_source"] == "deterministic_evidence_rule"
        ]
        self.assertEqual(
            [d["selected_action"] for d in decisions],
            ["inspect_missingness", "summarize_environment_stability"],
        )
        actual_tools = [item["tool_name"] for item in self.artifacts]
        self.assertLess(
            actual_tools.index("summarize_environment_stability"),
            actual_tools.index("analyze_trait_associations"),
        )
        follow = self.science["follow_up_analysis"]
        self.assertTrue(follow["executed"])
        self.assertTrue(follow["adaptively_selected"])
        rank = next(a for a in self.artifacts if a["tool_name"] == "rank_genotypes")
        self.assertEqual(follow["selection_evidence_ids"], [rank["artifact_id"]])

    def test_partial_missing_and_source_mismatch_do_not_create_evidence(self):
        partial = build_scientific_report(OBJECTIVE, self.artifacts[:1], [], {})
        self.assertEqual(partial["evidence_coverage"], "partial")
        self.assertTrue(
            all(h["verdict"] == "not_assessed" for h in partial["hypothesis_evaluations"])
        )
        self.assertEqual(partial["candidate_summaries"], [])
        counterexample = copy.deepcopy(self.artifacts)
        counterexample[-1]["source_sha256"] = "f" * 64
        mismatch = build_scientific_report(OBJECTIVE, counterexample, [], {})
        self.assertEqual(mismatch["evidence_coverage"], "source_mismatch")
        self.assertNotIn("findings", mismatch)
        self.assertTrue(all(not h["evidence_ids"] for h in mismatch["hypothesis_evaluations"]))

    def test_synthetic_direction_counterexample_and_constant_trait_are_not_optimistic(self):
        counterexample = copy.deepcopy(self.artifacts)
        traits = next(a for a in counterexample if a["tool_name"] == "analyze_trait_associations")[
            "results"
        ]["associations"]
        asi = next(a for a in traits if a["trait"] == "asi_days")
        asi["spearman_rho"] = 0.5
        asi["spearman_rho_95_percentile_interval"] = [0.2, 0.8]
        for env in asi["per_environment"]:
            env["spearman_rho"] = 0.5
        stay = next(a for a in traits if a["trait"] == "stay_green_score")
        stay["spearman_rho"] = None
        report = build_scientific_report("Synthetic counterexample only", counterexample, [], {})
        evaluations = {h["id"]: h for h in report["hypothesis_evaluations"]}
        self.assertEqual(evaluations["H2"]["verdict"], "criterion_not_met")
        self.assertEqual(len(evaluations["H2"]["contradictions"]), 3)
        self.assertEqual(evaluations["H3"]["verdict"], "inconclusive")

    def test_unassessed_custom_hypotheses_make_the_run_partial_and_preserve_original(self):
        store = RunStore(":memory:")
        try:
            config = configuration(
                hypotheses=["Custom hypothesis not covered by the fixed profile"]
            )
            result = ResearchAgent(
                load_ghana(), store, configuration=config, max_steps=6, max_tool_calls=6
            ).run("Keep this original")
            self.assertEqual(result["report"]["completion_status"], "partial")
            self.assertEqual(
                result["report"]["scientific_report"]["additional_hypotheses_not_assessed"],
                config.hypotheses,
            )
            self.assertEqual(result["report"]["objective"], "Keep this original")
        finally:
            store.close()

    def test_full_profile_contract_rejects_focused_or_forged_plans_and_preserves_budgets(self):
        with self.assertRaises(ValidationError):
            configuration(preferred_methods=["dataset_profile"])
        plan = build_deterministic_plan(OBJECTIVE, configuration())
        profile_plan_check(plan)
        plan.important_constraints = []
        with self.assertRaises(ValueError):
            profile_plan_check(plan)
        small = ResearchConfiguration(
            desired_outputs=[PROFILE_OUTPUT],
            constraints=ResearchConstraints(max_steps=1, max_tool_calls=1),
        )
        store = RunStore(":memory:")
        try:
            result = ResearchAgent(
                load_ghana(), store, configuration=small, max_steps=1, max_tool_calls=1
            ).run(OBJECTIVE)
            self.assertEqual(result["report"]["completion_status"], "partial")
            self.assertEqual(len(result["report"]["scientific_report"]["missing_tools"]), 5)
            self.assertEqual(len(result["report"]["research_plan"]["tasks"]), len(PROFILE_METHODS))
        finally:
            store.close()

    def test_followup_order_changes_when_observed_analytic_coverage_changes(self):
        from neurolab.research_context import ResearchTask

        pending = [
            ResearchTask(
                task_id="audit", title="Audit", description="Audit", tool_name="inspect_missingness"
            ),
            ResearchTask(
                task_id="compare",
                title="Compare",
                description="Compare",
                tool_name="compare_regimes",
            ),
        ]
        evidence = {
            "tool_name": "dataset_profile",
            "results": {
                "missingness": {
                    "grain_yield_value": {"missing": 0},
                    "location_code": {"missing": 864},
                }
            },
        }
        self.assertEqual(profile_followup(evidence, pending)[0], "compare_regimes")
        evidence["results"]["missingness"]["grain_yield_value"]["missing"] = 1
        self.assertEqual(profile_followup(evidence, pending)[0], "inspect_missingness")

    def test_current_source_inventory_and_reproducibility(self):
        inventory = self.science["dataset_inventory"]
        irrigation = next(
            source
            for source in inventory
            if source["source_file"].endswith("m28fulli_irrigation-data.csv")
        )
        self.assertEqual(
            (
                irrigation["physical_rows"],
                irrigation["fully_empty_rows"],
                irrigation["substantive_rows"],
            ),
            (337913, 336953, 960),
        )
        self.assertFalse(irrigation["analysis_enabled"])
        self.assertEqual(sum(source["analysis_enabled"] for source in inventory), 1)
        self.assertTrue(all(len(source["source_sha256"]) == 64 for source in inventory))
        self.assertEqual(len(self.science["inventory_manifest_sha256"]), 64)
        self.assertTrue(RUNTIME_PROVENANCE["module_sha256"])
        self.assertTrue(
            all(len(value) == 64 for value in RUNTIME_PROVENANCE["module_sha256"].values())
        )


class InventoryAndProvenanceBoundaryTests(unittest.TestCase):
    def test_source_byte_mismatch_and_outside_staging_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/raw").mkdir(parents=True)
            source = root / "data/raw/test.csv"
            source.write_text("a\n1\n")
            metadata = {
                "rows": 1,
                "fully_empty_rows": 0,
                "columns": ["a"],
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
            manifest = root / "data/manifest.json"
            manifest.write_text(json.dumps({"data/raw/test.csv": metadata}))
            self.assertEqual(len(source_inventory(root)["files"]), 1)
            source.write_text("a\n2\n")
            with self.assertRaises(ValueError):
                source_inventory(root)
            manifest.write_text(json.dumps({"../outside.csv": metadata}))
            with self.assertRaises(ValueError):
                source_inventory(root)

    def test_git_metadata_handles_refs_packed_detached_unknown_and_cycles_without_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git = root / ".git"
            (git / "refs/heads").mkdir(parents=True)
            head = git / "HEAD"
            ref = git / "refs/heads/main"
            revision = "a" * 40
            head.write_text("ref: refs/heads/main")
            ref.write_text(revision)
            self.assertEqual(git_revision(root), revision)
            ref.unlink()
            (git / "packed-refs").write_text(revision + " refs/heads/main\n")
            self.assertEqual(git_revision(root), revision)
            head.write_text(revision)
            self.assertEqual(git_revision(root), revision)
            head.write_text("unknown")
            self.assertIsNone(git_revision(root))
            head.write_text("ref: refs/heads/main")
            ref.write_text("ref: refs/heads/main")
            self.assertIsNone(git_revision(root))
            head.unlink()
            self.assertIsNone(git_revision(root))
