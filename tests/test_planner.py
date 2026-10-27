"""No-network research-plan contracts and unsupported-operation controls."""

import unittest
from pathlib import Path

from jsonschema import ValidationError
from pydantic import ValidationError as DraftValidationError

from neurolab.agent import ResearchAgent
from neurolab.ghana import load_ghana
from neurolab.planner import refine_plan, validate_execution_plan
from neurolab.research_context import ResearchConfiguration, ResearchDraft, build_deterministic_plan
from neurolab.store import RunStore

ROOT = Path(__file__).resolve().parents[1]


class RefinementFixture:
    provider = "test-fixture"
    model_id = "not-live-inference"

    def __init__(self, objective, config):
        self.objective = objective
        self.config = config
        self.messages = []

    def generate_refinement(self, messages, schema, *, timeout):
        self.messages = messages
        plan = build_deterministic_plan(self.objective, self.config).model_dump(mode="json")
        for key in ("objective_sha256", "planning_mode"):
            plan.pop(key)
        for task in plan["tasks"]:
            for key in ("status", "evidence_ids"):
                task.pop(key)
        for item in plan["dataset_suggestions"]:
            item.pop("enabled_for_analysis")
        plan["important_constraints"] = [
            "Do not combine unrelated trials",
            "No field recommendation",
        ]
        plan["unsupported_requirements"] = ["Confirmatory field validation"]
        return plan


class PlannerTests(unittest.TestCase):
    def test_refinement_preserves_full_original_and_returns_only_a_proposal(self):
        original = "# Original\r\n\n" + "λ" * 19985
        config = ResearchConfiguration()
        fixture = RefinementFixture(original, config)
        plan = refine_plan(original, config, fixture, timeout=5)
        self.assertIn(
            original.replace("\r", "\\r").replace("\n", "\\n"), fixture.messages[1]["content"]
        )
        self.assertEqual(plan.refined_objective, original)
        self.assertEqual(plan.planning_mode, "meta")
        self.assertEqual(plan.important_constraints[0], "Do not combine unrelated trials")
        self.assertTrue(
            all(task.status == "pending" and not task.evidence_ids for task in plan.tasks)
        )

    def test_duplicate_or_precompleted_tasks_cannot_be_accepted_as_new_evidence(self):
        plan = build_deterministic_plan("Investigate", ResearchConfiguration())
        plan.tasks[1].task_id = plan.tasks[0].task_id
        with self.assertRaises(ValueError):
            validate_execution_plan(plan, "Investigate")
        plan = build_deterministic_plan("Investigate", ResearchConfiguration())
        plan.tasks[0].status = "completed"
        with self.assertRaises(ValueError):
            validate_execution_plan(plan, "Investigate")

    def test_draft_cannot_save_an_accepted_plan_for_a_different_original(self):
        plan = build_deterministic_plan("Original A", ResearchConfiguration())
        with self.assertRaises(DraftValidationError):
            ResearchDraft(objective="Original B", accepted_plan=plan)

    def test_refinement_schema_rejects_extra_fields_before_planning(self):
        fixture = RefinementFixture("Investigate", ResearchConfiguration())
        fixture.generate_refinement = lambda *_args, **_kwargs: {"execute_shell": "forbidden"}
        with self.assertRaises(ValidationError):
            refine_plan("Investigate", fixture.config, fixture, timeout=5)

    def test_execution_preferences_produce_a_plan_only_report_without_numeric_tools(self):
        dataset = load_ghana(ROOT)
        config = ResearchConfiguration()
        config.autonomy_preferences.execute_supported_tasks = False
        store = RunStore(":memory:")
        try:
            result = ResearchAgent(dataset, store, configuration=config).run("Plan only")
            self.assertEqual(result["report"]["completion_status"], "plan_only")
            self.assertEqual(result["report"]["tool_calls"], 0)
            self.assertEqual(result["report"]["evidence_ids"], [])
            self.assertFalse(
                any(event["event_type"] == "tool.requested" for event in result["events"])
            )
        finally:
            store.close()
