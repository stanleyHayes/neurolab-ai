"""Hand-calculated synthetic oracles and separately labeled real-source checks."""

import copy
import dataclasses
import json
import unittest

from neurolab.agent import ResearchAgent
from neurolab.descriptive import (
    TRAITS,
    analyze_trait_associations,
    average_ranks,
    correlation,
    summarize_environment_stability,
)
from neurolab.ghana import load_ghana
from neurolab.research_context import ResearchConfiguration, ResearchConstraints
from neurolab.store import RunStore
from neurolab.tools import ToolValidationError, execute_tool


def synthetic():
    rows = []
    for regime in ["DROUGHT", "WELL_WATERED"]:
        for env in range(3):
            for genotype in range(4):
                for rep in range(2):
                    row = {
                        "genotype_id": chr(65 + genotype),
                        "environment_code": f"{regime}_{env}",
                        "water_regime": regime,
                        "grain_yield_value": 10 * (genotype + 1) + 5 * env + (2 * rep - 1),
                        "source_row_number": len(rows) + 2,
                    }
                    row.update({trait: 4 - genotype for trait in TRAITS})
                    row["stay_green_score"] = 4
                    rows.append(row)
    return dataclasses.replace(
        load_ghana(),
        records=tuple(rows),
        source_row_count=len(rows),
        source_file="synthetic-test-only.csv",
        source_sha256="a" * 64,
    )


class DescriptiveScienceTests(unittest.TestCase):
    def test_rank_ties_constant_and_undefined_correlation(self):
        self.assertEqual(average_ranks([3, 1, 1, 7]), [3, 1.5, 1.5, 4])
        self.assertAlmostEqual(correlation([1, 1, 3], [1, 2, 3], ranked=True), 3**0.5 / 2)
        self.assertIsNone(correlation([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(correlation([1, 2], [1, 2]))
        self.assertIsNone(correlation([1, 2, float("inf")], [1, 2, 3]))

    def test_environment_variation_matches_hand_oracle_and_centering(self):
        result = summarize_environment_stability(synthetic())["results"]["regimes"]["DROUGHT"]
        a = next(item for item in result["genotypes"] if item["genotype_id"] == "A")
        self.assertEqual(a["mean_yield_kg_ha"], 15)
        self.assertEqual(a["environment_mean_sd_kg_ha"], 5)
        self.assertAlmostEqual(a["environment_mean_cv_percent"], 100 / 3)
        self.assertEqual(a["environment_centered_sd_kg_ha"], 0)
        self.assertEqual(set(a["leave_one_environment_out_ranks"].values()), {4})
        self.assertEqual([item["plot_count"] for item in a["environment_means"]], [2, 2, 2])

    def test_missing_whole_environment_does_not_disappear_from_coverage(self):
        dataset = synthetic()
        for row in dataset.records:
            if row["environment_code"] == "DROUGHT_2":
                row["grain_yield_value"] = None
        result = summarize_environment_stability(dataset)["results"]["regimes"]["DROUGHT"]
        self.assertEqual(len(result["environment_codes"]), 3)
        self.assertEqual(result["complete_genotype_count"], 0)
        self.assertTrue(
            all(not entry["complete_environment_coverage"] for entry in result["genotypes"])
        )
        self.assertTrue(
            all(not entry["leave_one_environment_out_ranks"] for entry in result["genotypes"])
        )
        for entry in result["genotypes"]:
            self.assertTrue(
                all(
                    point["rank_among_complete_genotypes"] is None
                    for point in entry["environment_means"]
                )
            )

    def test_trait_pairs_have_genotype_units_and_constant_traits_are_null(self):
        result = analyze_trait_associations(synthetic(), bootstrap_samples=200)
        asi, stay_green = result["results"]["associations"][:2]
        self.assertEqual(asi["genotype_count"], 4)
        self.assertEqual(asi["spearman_rho"], -1)
        self.assertEqual(asi["pearson_r"], -1)
        self.assertEqual(asi["points"][0]["trait_mean"], 4)
        self.assertEqual(asi["points"][0]["yield_mean_kg_ha"], 15)
        self.assertIsNone(stay_green["spearman_rho"])
        self.assertIsNone(stay_green["spearman_rho_95_percentile_interval"])
        self.assertEqual(stay_green["valid_bootstrap_replicates"], 0)
        json.dumps(result, allow_nan=False)

    def test_trait_missingness_is_pairwise_complete_across_expected_environments(self):
        dataset = synthetic()
        for row in dataset.records:
            if row["genotype_id"] == "A" and row["environment_code"] == "DROUGHT_2":
                row["asi_days"] = None
        associations = analyze_trait_associations(dataset, bootstrap_samples=100)["results"][
            "associations"
        ]
        self.assertEqual(associations[0]["genotype_count"], 3)
        self.assertNotIn("A", [point["genotype_id"] for point in associations[0]["points"]])
        self.assertEqual(associations[1]["genotype_count"], 4)

    def test_real_source_reproducibility_lineage_and_no_mutation(self):
        dataset = load_ghana()
        before = copy.deepcopy(dataset.records)
        first = analyze_trait_associations(dataset, seed=17, bootstrap_samples=100)
        second = analyze_trait_associations(
            dataclasses.replace(dataset, records=tuple(reversed(dataset.records))),
            seed=17,
            bootstrap_samples=100,
        )
        self.assertEqual(first, second)
        self.assertEqual(dataset.records, before)
        self.assertNotEqual(
            first["artifact_id"],
            analyze_trait_associations(dataset, seed=18, bootstrap_samples=100)["artifact_id"],
        )
        for association in first["results"]["associations"]:
            self.assertEqual(association["genotype_count"], 72)
            self.assertEqual(
                sum(
                    len(env["source_row_numbers"])
                    for point in association["points"]
                    for env in point["environment_means"]
                ),
                432,
            )
            self.assertTrue(-1 <= association["spearman_rho"] <= 1)
        stable = summarize_environment_stability(dataset)
        self.assertEqual(stable["sample_size"], 864)
        self.assertEqual(stable["source_sha256"], dataset.source_sha256)
        self.assertEqual(stable["results"]["regimes"]["DROUGHT"]["complete_genotype_count"], 72)

    def test_strict_registry_and_replay_integration(self):
        dataset = load_ghana()

        def call(action, parameters):
            return {
                "action": action,
                "parameters": parameters,
                "trace_id": "test",
                "hypothesis_id": "test",
                "dataset_id": "ghana_combined",
            }

        artifact = execute_tool(
            call("analyze_trait_associations", {"bootstrap_samples": 100}), dataset, seed=17
        )
        self.assertEqual(artifact["sample_size"], 432)
        invalid_parameters = call("summarize_environment_stability", {"bootstrap_samples": 100})
        with self.assertRaises(ToolValidationError):
            execute_tool(invalid_parameters, dataset, seed=17)
        invalid_budget = call("analyze_trait_associations", {"bootstrap_samples": True})
        with self.assertRaises(ToolValidationError):
            execute_tool(invalid_budget, dataset, seed=17)
        store = RunStore(":memory:")
        try:
            configuration = ResearchConfiguration(
                preferred_methods=["environment_stability", "trait_associations"],
                constraints=ResearchConstraints(max_steps=2, max_tool_calls=2),
            )
            run = ResearchAgent(
                dataset, store, configuration=configuration, max_steps=2, max_tool_calls=2
            ).run(
                "Explore observed environment variation and genotype trait associations without model calls"
            )
            self.assertEqual(run["report"]["completion_status"], "complete")
            self.assertEqual(len(run["report"]["grounded_claims"]), 2)
            self.assertIn("not validated", run["report"]["grounded_claims"][0]["claim"])
            self.assertEqual(run["report"]["mode"], "deterministic_replay")
        finally:
            store.close()

    def test_budget_and_missing_identity_reject_before_inventing_results(self):
        budget_dataset = synthetic()
        for value in [99, 10001, True, 100.5]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze_trait_associations(budget_dataset, bootstrap_samples=value)
        dataset = synthetic()
        dataset.records[0]["environment_code"] = None
        with self.assertRaises(ValueError):
            analyze_trait_associations(dataset, bootstrap_samples=100)
        with self.assertRaises(ValueError):
            summarize_environment_stability(dataset)


class EvidenceContextTests(unittest.TestCase):
    def test_new_tools_forward_computed_summaries_without_plot_level_context_bloat(self):
        class FixtureAdapter:
            provider = "test-fixture"
            model_id = "not-live-inference"

            def __init__(self):
                self.contexts = []

            def generate_structured(self, messages, schema, *, timeout):
                context = json.loads(messages[1]["content"])
                self.contexts.append(context)
                return {
                    "action": context["context"]["active_plan_tasks"][0]["tool_name"],
                    "bootstrap_samples": None,
                    "decision_summary": "Fixture selects the next supported task.",
                }

        adapter = FixtureAdapter()
        config = ResearchConfiguration(
            preferred_methods=["trait_associations", "environment_stability"],
            constraints=ResearchConstraints(max_steps=2, max_tool_calls=2),
        )
        store = RunStore(":memory:")
        try:
            run = ResearchAgent(
                load_ghana(),
                store,
                mode="meta",
                model_adapter=adapter,
                configuration=config,
                max_steps=2,
                max_tool_calls=2,
            ).run("Fixture-only context boundary test")
            self.assertEqual(run["report"]["completion_status"], "complete")
            association = adapter.contexts[1]["evidence"][0]["results"]["associations"][0]
            self.assertNotIn("points", association)
            self.assertIn("spearman_rho", association)
            self.assertIn("genotype_count", association)
            self.assertTrue(
                any("exchangeable" in warning for warning in run["report"]["limitations"])
            )
        finally:
            store.close()
