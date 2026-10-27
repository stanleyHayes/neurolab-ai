"""Programmed generation contracts and actual-data context projections; no inference."""

import copy
import json
import unittest

from jsonschema import ValidationError

from neurolab.action_selection import selection_schema, validated_selection
from neurolab.ghana import load_ghana
from neurolab.model_evidence import evidence_results
from neurolab.tools import REGISTRY, execute_tool


class ActionSelectionTests(unittest.TestCase):
    def test_action_specific_schema_rejects_the_actual_live_invalid_pair(self):
        schema = selection_schema(REGISTRY)
        for action in REGISTRY:
            for samples in (None, 1000):
                response = {
                    "choice": {"action": action, "bootstrap_samples": samples},
                    "decision_summary": "Programmed contract probe, not model reasoning.",
                }
                if samples and action not in {"compare_regimes", "analyze_trait_associations"}:
                    with self.assertRaises(ValidationError):
                        validated_selection(response, schema)
                else:
                    self.assertEqual(validated_selection(response, schema)["action"], action)

    def test_completed_disallowed_and_malformed_choices_cannot_pass(self):
        schema = selection_schema(["rank_genotypes"])
        for choice in (
            {"action": "dataset_profile", "bootstrap_samples": None},
            {"action": "execute_shell", "bootstrap_samples": None},
            {"action": "rank_genotypes", "bootstrap_samples": None, "code": "unsafe"},
        ):
            response = {"choice": choice, "decision_summary": "Fixture"}
            with self.assertRaises(ValidationError):
                validated_selection(response, schema)
        with self.assertRaises(ValueError):
            selection_schema([])

    def test_real_source_projections_preserve_values_and_full_artifacts(self):
        dataset = load_ghana()
        artifacts = []
        for action in ("dataset_profile", "rank_genotypes"):
            artifact = execute_tool(
                {
                    "trace_id": "context-test",
                    "hypothesis_id": "test",
                    "dataset_id": "ghana_combined",
                    "action": action,
                    "parameters": {},
                },
                dataset,
                seed=2026,
            )
            snapshot = copy.deepcopy(artifact)
            projection = evidence_results(artifact)
            self.assertEqual(artifact, snapshot)
            self.assertLess(len(json.dumps(projection)), len(json.dumps(artifact["results"])) / 2)
            self.assertIn("context_projection", projection)
            artifacts.append((artifact, projection))
        profile, projection = artifacts[0]
        self.assertEqual(projection["row_count"], 864)
        self.assertEqual(projection["source_sha256"], profile["source_sha256"])
        ranking, projection = artifacts[1]
        self.assertEqual(projection["genotype_count"], 72)
        self.assertEqual(projection["leading_genotypes"], ranking["results"]["genotypes"][:5])
        self.assertEqual(projection["trailing_genotypes"], ranking["results"]["genotypes"][-5:])

    def test_full_original_objective_context_fits_reviewed_bounded_requests(self):
        from neurolab.agent import ResearchAgent
        from neurolab.store import RunStore

        objective = (
            "Investigate which maize genotypes demonstrate the strongest drought tolerance "
            "while maintaining relatively stable grain yield across the available experimental "
            "environments. Form hypotheses, select appropriate statistical analyses, execute "
            "the analyses, evaluate the evidence, and recommend the next experiment."
        )

        class RecordingFixture:
            provider = "test-fixture"
            model_id = "not-live-inference"

            def __init__(self):
                self.inputs = []

            def generate_structured(self, messages, schema, *, timeout):
                self.inputs.append((messages, schema))
                context = json.loads(messages[1]["content"])
                action = context["context"]["active_plan_tasks"][0]["tool_name"]
                return {
                    "choice": {"action": action, "bootstrap_samples": None},
                    "decision_summary": "Programmed bounded-context contract, not Meta reasoning.",
                }

        fixture = RecordingFixture()
        store = RunStore(":memory:")
        try:
            result = ResearchAgent(
                load_ghana(),
                store,
                mode="meta",
                model_adapter=fixture,
                max_steps=6,
                max_tool_calls=6,
            ).run(objective, seed=2026)
            self.assertEqual(result["run"]["status"], "COMPLETE")
            self.assertEqual(len(fixture.inputs), 6)
            reserved = 0
            for messages, schema in fixture.inputs:
                self.assertEqual(json.loads(messages[1]["content"])["objective"], objective)
                request = {
                    "messages": messages,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "research_action",
                            "strict": True,
                            "schema": schema,
                        },
                    },
                }
                reserved += (
                    len(json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode())
                    + 1024
                    + 1000
                )
            # Leave headroom for the separate 4000-output-token planning request.
            self.assertLess(reserved, 80000)
            ranking = next(
                a
                for a in store.list_artifacts(result["run"]["run_id"])
                if a["tool_name"] == "rank_genotypes"
            )
            self.assertEqual(len(ranking["results"]["genotypes"]), 72)
        finally:
            store.close()
