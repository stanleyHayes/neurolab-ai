import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import basic from "../fixtures/ghana-ui.json";
import descriptive from "../fixtures/ghana-descriptive-ui.json";
import {
  EnvironmentYieldPlot,
  GenotypeMiniPlot,
  MetricVisual,
  TraitAssociationPlot,
} from "../../app/workspace/EvidenceVisualizations";

type Row = Record<string, unknown>;
const associations = descriptive.artifacts[0].results.associations! as Row[];
const regimes = descriptive.artifacts[1].results.regimes!;
const drought = regimes.DROUGHT;

it("shows retention above 100 without clipping it to a full-percent gauge", () => {
  const { container } = render(
    <MetricVisual
      value={125}
      maximum={100}
      reference={100}
      description="Yield retention percent"
    />,
  );
  expect(screen.getByRole("img").getAttribute("aria-label")).toContain(
    "scale 0 to 125; reference 100",
  );
  expect(
    Number(
      container.querySelector(".metric-visual-fill")?.getAttribute("width"),
    ),
  ).toBe(238);
  expect(container.querySelector("path")?.getAttribute("d")).toBe(
    "M191.4 3v22",
  );
});

it("withholds numeric graphics for missing or invalid measures", () => {
  const { rerender } = render(
    <MetricVisual value={null} maximum={100} description="Missing" />,
  );
  expect(screen.queryByRole("img")).toBeNull();
  rerender(
    <MetricVisual value={Number.NaN} maximum={100} description="Invalid" />,
  );
  expect(screen.queryByRole("img")).toBeNull();
});

it("plots each saved genotype mean in its recorded order", () => {
  const ranking = basic.artifacts.find(
    (artifact) => artifact.tool_name === "rank_genotypes",
  )!;
  const entries = ranking.results.genotypes! as Row[];
  const { container } = render(<GenotypeMiniPlot entries={entries} />);
  const bars = container.querySelectorAll("rect");
  expect(bars).toHaveLength(entries.length);
  expect(bars[0].textContent).toContain(entries[0].genotype_id);
  const maximum = Math.max(
    ...entries.map((entry) => Number(entry.equal_environment_mean_yield_kg_ha)),
    1,
  );
  expect(Number(bars[0].getAttribute("height"))).toBeCloseTo(
    (34 * Number(entries[0].equal_environment_mean_yield_kg_ha)) / maximum,
  );
});

it("positions trait dots and intervals from actual recorded coefficients", () => {
  const { container } = render(
    <TraitAssociationPlot associations={associations} />,
  );
  const rho = Number(associations[0].spearman_rho);
  const interval = associations[0]
    .spearman_rho_95_percentile_interval as number[];
  const first = container.querySelector("svg")!;
  expect(Number(first.querySelector("circle")?.getAttribute("cx"))).toBeCloseTo(
    12 + (rho + 1) * 148,
  );
  expect(
    first.querySelector(".comparison-range path")?.getAttribute("d"),
  ).toContain(
    `M${12 + (interval[0] + 1) * 148} 18H${12 + (interval[1] + 1) * 148}`,
  );
  expect(
    screen.getByText(/An interval crossing zero includes both directions/),
  ).toBeTruthy();
});

it("draws no dot or invented interval for an absent correlation", () => {
  const { container } = render(
    <TraitAssociationPlot
      associations={[
        {
          trait: "asi_days",
          spearman_rho: null,
          spearman_rho_95_percentile_interval: null,
        },
      ]}
    />,
  );
  expect(container.querySelector("circle")).toBeNull();
  expect(screen.getByText("Not recorded")).toBeTruthy();
});

it("uses recorded environment means, distinct symbols and a labeled zero-based domain", () => {
  const entries = drought.genotypes as Row[];
  const { container } = render(
    <EnvironmentYieldPlot
      entries={entries}
      environments={drought.environment_codes}
      regime="DROUGHT"
    />,
  );
  expect(screen.getAllByRole("img")).toHaveLength(8);
  const first = container.querySelector("svg")!;
  const points = entries[0].environment_means as Row[];
  const maximum =
    Math.ceil(
      Math.max(
        ...entries
          .slice(0, 8)
          .flatMap((entry) =>
            (entry.environment_means as Row[]).map((point) =>
              Number(point.mean_yield_kg_ha),
            ),
          ),
      ) / 1000,
    ) * 1000;
  expect(Number(first.querySelector("circle")?.getAttribute("cx"))).toBeCloseTo(
    12 + (Number(points[0].mean_yield_kg_ha) / maximum) * 296,
  );
  expect(first.querySelector("rect")).toBeTruthy();
  expect(first.querySelector(".environment-point-2 path")).toBeTruthy();
  expect(
    screen.getByText(/not a confidence interval or a future prediction/),
  ).toBeTruthy();
});
