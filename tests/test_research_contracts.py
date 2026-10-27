"""Regression coverage for exact objectives, plans, budgets and truthful status."""

import json
import os
import unittest
from pathlib import Path

from pydantic import ValidationError

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
from neurolab.agent import ResearchAgent
from neurolab.ghana import load_ghana
from neurolab.providers import ModelContextLimitError, OpenAICompatibleAdapter
from neurolab.research_context import (
    ResearchConfiguration,
    ResearchConstraints,
    ResearchRunRequest,
    build_deterministic_plan,
    estimated_context_tokens_upper_bound,
)
from neurolab.store import RunStore
from neurolab.tools import REGISTRY, SCHEMA, ToolValidationError, validate_tool_call

ROOT = Path(__file__).resolve().parents[1]


class PendingTaskAdapter:
    """Fixture only: select a pending tool using the supplied persisted context."""

    provider = "test-fixture"
    model_id = "not-live-inference"

    def __init__(self):
        self.contexts = []

    def generate_structured(self, messages, schema, *, timeout):
        context = json.loads(messages[1]["content"])
        self.contexts.append(context)
        action = context["context"]["active_plan_tasks"][0]["tool_name"]
        return {
            "action": action,
            "bootstrap_samples": 100 if action == "compare_regimes" else None,
            "decision_summary": "Fixture selects the next pending analysis.",
        }


class ResearchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def setUp(self):
        self.store = RunStore(":memory:")

    def tearDown(self):
        self.store.close()

    def test_legacy_and_structured_requests_reconcile_budgets(self):
        request = ResearchRunRequest(
            objective="exact",
            configuration=ResearchConfiguration(
                constraints=ResearchConstraints(max_steps=1, max_tool_calls=1, max_seconds=7)
            ),
        )
        self.assertEqual(request.constraints.max_seconds, 7)
        conflicting_constraints = ResearchConstraints()
        default_configuration = ResearchConfiguration()
        with self.assertRaises(ValidationError):
            ResearchRunRequest(
                objective="exact",
                constraints=conflicting_constraints,
                configuration=request.configuration,
            )
        with self.assertRaises(ValidationError):
            ResearchRunRequest(
                objective="exact", dataset_id="iita_drought", configuration=default_configuration
            )

    def test_model_sees_only_pending_tasks_and_exact_objective(self):
        objective = "Observe drought patterns\n" + "α maize constraints " * 500
        adapter = PendingTaskAdapter()
        result = ResearchAgent(self.dataset, self.store, mode="meta", model_adapter=adapter).run(
            objective
        )
        self.assertEqual(result["report"]["completion_status"], "complete")
        self.assertEqual(result["run"]["status"], "COMPLETE")
        self.assertEqual(len(adapter.contexts), 3)
        for index, context in enumerate(adapter.contexts):
            self.assertEqual(context["objective"], objective if index == 0 else None)
            self.assertEqual(len(context["context"]["active_plan_tasks"]), 3 - index)
            self.assertEqual(len(context["evidence"]), index)
        self.assertTrue(
            all(task["status"] == "completed" for task in result["run"]["research_plan"]["tasks"])
        )
        self.assertFalse(
            any(event["event_type"] == "hypothesis.proposed" for event in result["events"])
        )

    def test_budget_exhaustion_produces_partial_terminal_event(self):
        result = ResearchAgent(self.dataset, self.store, max_steps=1).run("Compare and rank")
        self.assertEqual(result["report"]["completion_status"], "partial")
        self.assertEqual(result["run"]["status"], "PARTIAL")
        self.assertEqual(result["events"][-1]["event_type"], "run.partial")
        self.assertFalse(any(event["event_type"] == "run.completed" for event in result["events"]))

    def test_replay_honors_selected_method_and_preserves_plan_input(self):
        config = ResearchConfiguration(preferred_methods=["missingness_audit"])
        plan = build_deterministic_plan("Missing values only", config)
        result = ResearchAgent(
            self.dataset, self.store, configuration=config, research_plan=plan
        ).run("Missing values only")
        self.assertEqual(
            [a["tool_name"] for a in self.store.list_artifacts(result["run"]["run_id"])],
            ["inspect_missingness"],
        )
        self.assertEqual(result["report"]["completion_status"], "complete")
        self.assertEqual(plan.tasks[0].status, "pending")

    def test_schema_matches_dispatch_and_rejects_irrelevant_parameters(self):
        self.assertEqual(set(SCHEMA["properties"]["action"]["enum"]), set(REGISTRY))
        with self.assertRaises(ToolValidationError):
            validate_tool_call(
                {
                    "trace_id": "t",
                    "hypothesis_id": "h",
                    "dataset_id": "ghana_combined",
                    "action": "dataset_profile",
                    "parameters": {"bootstrap_samples": 100},
                }
            )

    def test_context_limit_rejects_before_transport_without_truncation(self):
        messages = [{"role": "user", "content": "α" * 10000}]
        self.assertGreater(estimated_context_tokens_upper_bound(messages), 20000)
        adapter = OpenAICompatibleAdapter(
            endpoint="https://provider.invalid",
            api_key="fixture",
            model_id="fixture",
            max_context_tokens=16000,
        )
        with self.assertRaises(ModelContextLimitError):
            adapter.generate_structured(messages, {"type": "object"}, timeout=1)
        self.assertEqual(adapter.tokens_reserved, 0)


class PlanBudgetCompletenessTests(unittest.TestCase):
    def test_explicit_methods_are_not_silently_dropped_by_call_budget(self):
        config = ResearchConfiguration(
            preferred_methods=["dataset_profile", "trait_associations", "environment_stability"],
            constraints=ResearchConstraints(max_steps=1, max_tool_calls=1),
        )
        plan = build_deterministic_plan("Investigate all selected methods", config)
        self.assertEqual(len(plan.tasks), 3)
        store = RunStore(":memory:")
        try:
            run = ResearchAgent(
                load_ghana(ROOT), store, configuration=config, max_steps=1, max_tool_calls=1
            ).run("Investigate all selected methods")
            self.assertEqual(run["report"]["completion_status"], "partial")
            self.assertEqual(
                sum(
                    task["status"] == "pending" for task in run["report"]["research_plan"]["tasks"]
                ),
                2,
            )
        finally:
            store.close()
