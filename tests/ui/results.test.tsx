import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-ui.json";
import { EvidenceResults } from "../../app/workspace/EvidenceResults";
import { ResultInterval } from "../../app/workspace/ResultInterval";
import type {
  ResearchArtifact,
  ResearchReport,
} from "../../app/workspace/workspace-types";

const format = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("en-US", { maximumFractionDigits: 1 })
    : "—";
function resultsProps() {
  const artifacts = fixture.artifacts as ResearchArtifact[];
  const contrast = artifacts.find(
    (item) => item.tool_name === "compare_regimes",
  )!;
  const ranking = artifacts.find(
    (item) => item.tool_name === "rank_genotypes",
  )!;
  return {
    section: "research-results" as const,
    artifacts,
    report: fixture.report as ResearchReport,
    events: fixture.events,
    retrieving: false,
    showContrast: true,
    showRanking: true,
    contrast,
    ranking,
    resultValues: contrast.results,
    means: contrast.results.mean_yield_by_regime as Record<string, unknown>,
    topGenotypes: (
      ranking.results.genotypes as Array<Record<string, unknown>>
    ).slice(0, 12),
    contrastCI: contrast.uncertainty?.yield_difference_95_ci_kg_ha,
    formatNumber: format,
    downloadFile: vi.fn(),
  };
}

it("presents exactly the saved yield estimates and interval with accessible units", () => {
  const props = resultsProps();
  render(<EvidenceResults {...props} />);
  const values = props.contrast.results;
  expect(
    screen.getByRole("heading", { name: "Drought vs well-watered" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("img", {
      name: new RegExp(`difference ${format(values.yield_difference_kg_ha)}`),
    }),
  ).toBeTruthy();
  expect(
    screen.getByText(
      `${format((props.contrastCI as number[])[0])} to ${format((props.contrastCI as number[])[1])} kg/ha`,
    ),
  ).toBeTruthy();
  expect(screen.getAllByRole("definition")).toHaveLength(8);
});

it("shows leading observed genotypes and expands to every recorded row without resorting", () => {
  const props = resultsProps();
  render(<EvidenceResults {...props} />);
  const table = screen.getByRole("table", {
    name: /Descriptive drought genotype yields/,
  });
  expect(within(table).getAllByRole("row")).toHaveLength(9);
  const all = props.ranking.results.genotypes as Array<Record<string, unknown>>;
  fireEvent.click(
    screen.getByRole("button", { name: `Show all ${all.length} genotypes` }),
  );
  const rows = within(table).getAllByRole("row");
  expect(rows).toHaveLength(all.length + 1);
  expect(rows[1].textContent).toContain(all[0].genotype_id);
  expect(rows.at(-1)?.textContent).toContain(all.at(-1)?.genotype_id);
  expect(
    screen.getByText("Ranking uncertainty was not estimated."),
  ).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Show leading genotypes" }),
  );
  expect(within(table).getAllByRole("row")).toHaveLength(9);
});

it("exports the underlying artifacts and exposes the full immutable source identity", () => {
  const props = resultsProps();
  render(<EvidenceResults {...props} />);
  fireEvent.click(screen.getByText("Trace this result to its source"));
  expect(screen.getByText(fixture.report.source_sha256)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Export evidence JSON" }));
  expect(props.downloadFile).toHaveBeenCalledWith(
    `neurolab-${fixture.report.run_id}.json`,
    {
      report: fixture.report,
      artifacts: fixture.artifacts,
      events: fixture.events,
    },
    "application/json",
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Export artifact index CSV" }),
  );
  expect(props.downloadFile).toHaveBeenLastCalledWith(
    expect.stringMatching(/\.csv$/),
    expect.stringContaining(props.contrast.artifact_id),
    "text/csv",
  );
});

it("withholds comparisons when the report and artifact sources disagree", () => {
  const props = resultsProps();
  render(
    <EvidenceResults
      {...props}
      report={{ ...props.report, source_sha256: "different-source" }}
    />,
  );
  expect(screen.getByRole("alert").textContent).toContain(
    "source hashes do not match",
  );
  expect(
    screen.queryByRole("heading", { name: "Drought vs well-watered" }),
  ).toBeNull();
  expect(screen.queryByRole("table")).toBeNull();
});

it("does not turn missing intervals into zero-width scientific evidence", () => {
  render(
    <ResultInterval estimate={null} interval={null} formatNumber={format} />,
  );
  expect(
    screen.getByText("No valid interval was recorded for this result."),
  ).toBeTruthy();
  expect(screen.queryByRole("img")).toBeNull();
});

it("distinguishes partial artifacts and absent requested outputs", () => {
  const props = resultsProps();
  render(
    <EvidenceResults
      {...props}
      ranking={undefined}
      topGenotypes={[]}
      report={{ ...props.report, completion_status: "partial" }}
    />,
  );
  expect(
    screen.getByText(/Partial report: requested analyses remain incomplete/),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "No genotype summaries in this run" }),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "Drought vs well-watered" }),
  ).toBeTruthy();
});

it("distinguishes unreadable evidence from an empty run and withholds cached results", () => {
  render(<EvidenceResults {...resultsProps()} loadError />);
  expect(screen.getByText("Evidence unavailable")).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "Saved evidence couldn’t be loaded" }),
  ).toBeTruthy();
  expect(screen.getByText(/Use Reload run above/)).toBeTruthy();
  expect(screen.queryByText(/saved artifacts/)).toBeNull();
  expect(
    screen.queryByRole("link", { name: /Start an investigation/ }),
  ).toBeNull();
  expect(screen.queryByRole("link", { name: /Cinematic replay/ })).toBeNull();
  expect(
    screen.queryByRole("heading", { name: "Drought vs well-watered" }),
  ).toBeNull();
  expect(screen.queryByText(/This run has no comparison/)).toBeNull();
  expect(screen.queryByRole("button", { name: /Download/ })).toBeNull();
});
