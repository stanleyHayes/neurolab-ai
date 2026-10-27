"""Regenerate real-source UI fixtures: python -m scripts.generate_science_fixtures.

Uses an isolated in-memory store and deterministic numeric tools, never Meta.
UUIDs/timestamps/code snapshots change; this is not a performance benchmark.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args

from neurolab.agent import ResearchAgent
from neurolab.descriptive import analyze_trait_associations, summarize_environment_stability
from neurolab.ghana import load_ghana
from neurolab.research_context import DesiredOutput, ResearchConfiguration, ResearchConstraints
from neurolab.store import RunStore

ROOT = Path(__file__).resolve().parents[1]


def main():
    dataset = load_ghana(ROOT)
    store = RunStore(":memory:")
    try:
        objective = (ROOT / "tests/fixtures/ghana-research-objective.txt").read_text()
        configuration = ResearchConfiguration(
            desired_outputs=list(get_args(DesiredOutput)),
            constraints=ResearchConstraints(max_steps=6, max_tool_calls=6, max_seconds=180),
        )
        run = ResearchAgent(
            dataset,
            store,
            configuration=configuration,
            max_steps=6,
            max_tool_calls=6,
            max_wall_time=180,
        ).run(objective)
        fixture = {
            "fixture_label": "Actual deterministic Ghana full-profile execution; retrospective template evaluation, not Meta inference or a field trial",
            "report": run["report"],
            "events": store.list_events(run["report"]["run_id"]),
        }
        (ROOT / "tests/fixtures/ghana-investigation-ui.json").write_text(
            json.dumps(fixture, indent=2) + "\n"
        )
        descriptive = {
            "fixture_label": "Actual deterministic Ghana numeric tools; not Meta inference or synthetic crop data",
            "artifacts": [
                analyze_trait_associations(dataset, seed=2026, bootstrap_samples=1000),
                summarize_environment_stability(dataset),
            ],
        }
        (ROOT / "tests/fixtures/ghana-descriptive-ui.json").write_text(
            json.dumps(descriptive, indent=2) + "\n"
        )
        print(
            f"Generated actual-source fixtures: {run['report']['tool_calls']} tools, {len(fixture['events'])} persisted events, mode={run['report']['mode']}"
        )
    finally:
        store.close()


if __name__ == "__main__":
    main()
