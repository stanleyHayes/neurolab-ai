"""Actual-source numeric criteria with programmed planning; no inference claims."""

import copy
import unittest

from jsonschema import Draft202012Validator, ValidationError
from pydantic import ValidationError as ModelValidationError

from neurolab.agent import ResearchAgent
from neurolab.ghana import load_ghana
from neurolab.hypothesis_contracts import HypothesisTest, generation_schema, validate_tests
from neurolab.planner import refine_plan
from neurolab.research_context import ResearchConfiguration, build_deterministic_plan
from neurolab.scientific_report import build_scientific_report
from neurolab.store import RunStore

OBJECTIVE = (
    "Investigate which maize genotypes demonstrate the strongest drought tolerance "
    "while maintaining relatively stable grain yield across the available experimental "
    "environments. Form hypotheses, select appropriate statistical analyses, execute "
    "the analyses, evaluate the evidence, and recommend the next experiment."
)
SPECS = [
    {
        "id": "H7",
        "kind": "consistent_high_yield",
        "rank_fraction": 0.1,
        "leading_count": None,
        "trait": None,
        "rationale": "Programmed test: examine consistent high observed yield.",
    },
    {
        "id": "H8",
        "kind": "negative_trait_association",
        "rank_fraction": None,
        "leading_count": None,
        "trait": "asi_days",
        "rationale": "Programmed test: distinguish directional association from inconclusive evidence.",
    },
    {
        "id": "H9",
        "kind": "leading_rank_sensitivity",
        "rank_fraction": 0.2,
        "leading_count": 4,
        "trait": None,
        "rationale": "Programmed test: quantify environment-composition uncertainty.",
    },
]


class PlanningFixture:
    provider = "test-fixture"
    model_id = "not-live-inference"

    def generate_refinement(self, messages, schema, *, timeout):
        plan = build_deterministic_plan(OBJECTIVE, ResearchConfiguration()).model_dump(mode="json")
        for key in ("objective_sha256", "planning_mode"):
            plan.pop(key)
        for task in plan["tasks"]:
            task.pop("status")
            task.pop("evidence_ids")
        for suggestion in plan["dataset_suggestions"]:
            suggestion.pop("enabled_for_analysis")
        plan.update(
            hypotheses=[],
            hypothesis_tests=copy.deepcopy(SPECS),
            important_constraints=["Fixture-only structured proposal; never Meta authorship"],
        )
        return plan


class HypothesisContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana()

    def plan(self, config=None):
        return refine_plan(
            OBJECTIVE, config or ResearchConfiguration(), PlanningFixture(), timeout=5
        )

    def test_schema_and_server_reject_unexecutable_or_forged_results(self):
        schema = generation_schema()
        validator = Draft202012Validator(schema)
        validator.validate(SPECS)
        for update in (
            {"rank_fraction": 0.5},
            {"trait": "asi_days"},
            {"verdict": "criterion_met"},
            {"kind": "execute_code"},
        ):
            data = {**SPECS[0], **update}
            with self.subTest(update=update):
                with self.assertRaises(ValidationError):
                    validator.validate([data])
                with self.assertRaises(ModelValidationError):
                    HypothesisTest.model_validate(data)
        tests = [HypothesisTest.model_validate(x) for x in SPECS]
        with self.assertRaises(ValueError):
            validate_tests([tests[0], tests[0]])

    def test_actual_source_assesses_exact_parameters_and_preserves_provenance(self):
        store = RunStore(":memory:")
        try:
            plan = self.plan()
            result = ResearchAgent(
                self.dataset, store, research_plan=plan, max_steps=6, max_tool_calls=6
            ).run(OBJECTIVE)
            report = result["report"]
            science = report["scientific_report"]
            self.assertEqual(result["run"]["status"], "COMPLETE")
            self.assertEqual(report["objective"], OBJECTIVE)
            self.assertEqual(science["additional_hypotheses_not_assessed"], [])
            evaluations = science["hypothesis_evaluations"]
            self.assertEqual([e["id"] for e in evaluations], ["H7", "H8", "H9"])
            self.assertEqual(evaluations[0]["rank_threshold"], 8)
            self.assertEqual(evaluations[1]["verdict"], "inconclusive")
            self.assertEqual(evaluations[2]["range_width_threshold"], 15)
            self.assertEqual(len(evaluations[2]["rank_ranges"]), 4)
            ids = set(report["evidence_ids"])
            self.assertTrue(
                all(e["evidence_ids"] and set(e["evidence_ids"]).issubset(ids) for e in evaluations)
            )
            prepared = next(
                e for e in result["events"] if e["event_type"] == "research.investigation_prepared"
            )
            first_tool = min(
                e["sequence"] for e in result["events"] if e["event_type"] == "tool.requested"
            )
            self.assertLess(prepared["sequence"], first_tool)
            self.assertEqual(prepared["payload"]["source"], "accepted_structured_plan")
            self.assertEqual(len(prepared["payload"]["hypotheses"]), 3)
            self.assertTrue(science["next_experiment"])
            self.assertTrue(science["candidate_summaries"])
            self.assertEqual(science["conclusion_status"], "exploratory_not_field_validated")
            artifacts = store.list_artifacts(report["run_id"])
            from scripts.export_investigation import validate_bundle

            bundle = {
                "bundle_version": "neurolab-evidence-v1",
                "report": report,
                "artifacts": artifacts,
                "events": result["events"],
            }
            validated, _ = validate_bundle(bundle)
            self.assertEqual(
                validated["scientific_report"]["hypothesis_tests"][0]["rank_fraction"], 0.1
            )
            altered = copy.deepcopy(bundle)
            altered["report"]["research_plan"]["hypothesis_tests"][0]["rank_fraction"] = 0.2
            with self.assertRaises(ValueError):
                validate_bundle(altered)
            artifacts[0]["source_sha256"] = "different"
            mismatch = build_scientific_report(
                OBJECTIVE, artifacts, [], {}, plan.hypotheses, plan.hypothesis_tests
            )
            self.assertEqual(mismatch["evidence_coverage"], "source_mismatch")
            self.assertEqual(
                [e["id"] for e in mismatch["hypothesis_evaluations"]], ["H7", "H8", "H9"]
            )
            self.assertTrue(
                all(e["verdict"] == "not_assessed" for e in mismatch["hypothesis_evaluations"])
            )
        finally:
            store.close()

    def test_missing_method_rejected_before_execution_and_user_hypotheses_remain_partial(self):
        store = RunStore(":memory:")
        try:
            plan = self.plan()
            plan.tasks.pop()
            agent = ResearchAgent(self.dataset, store, research_plan=plan)
            with self.assertRaises(ValueError):
                agent.run(OBJECTIVE)
            config = ResearchConfiguration(
                hypotheses=["Additional user criterion requiring unavailable evidence"]
            )
            plan = self.plan(config)
            result = ResearchAgent(
                self.dataset,
                store,
                configuration=config,
                research_plan=plan,
                max_steps=6,
                max_tool_calls=6,
            ).run(OBJECTIVE)
            self.assertEqual(result["run"]["status"], "PARTIAL")
            self.assertEqual(
                result["report"]["scientific_report"]["additional_hypotheses_not_assessed"],
                config.hypotheses,
            )
        finally:
            store.close()
