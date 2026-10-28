import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-investigation-ui.json";
import { ScientificReportView } from "../../app/workspace/ScientificReportView";
import type { ResearchReport } from "../../app/workspace/workspace-types";
const report = fixture.report as ResearchReport;

it("presents actual hypothesis evaluations, contradictions and conditional scope without turning workflow completion into validation", () => {
  render(<ScientificReportView report={report} downloadFile={vi.fn()} />);
  const hypotheses = screen.getByRole("region", {
    name: "Hypothesis evaluations",
  });
  expect(within(hypotheses).getAllByRole("article")).toHaveLength(4);
  expect(within(hypotheses).getByText("Inconclusive")).toBeTruthy();
  expect(
    within(hypotheses).getByText(
      "The conditional resampling interval includes zero.",
    ),
  ).toBeTruthy();
  expect(
    screen.getByText(/Completing the workflow does not establish/),
  ).toBeTruthy();
  expect(screen.getByText(/Source score direction is unverified/)).toBeTruthy();
  expect(screen.getByText(/Selected using observed evidence/)).toBeTruthy();
  const traits = screen.getByRole("region", {
    name: "Seven-trait exploratory screen",
  });
  expect(within(traits).getByText(/plant_height_value/)).toBeTruthy();
  expect(
    within(traits).getByRole("table", { name: /Seven-trait screen/ }),
  ).toBeTruthy();
  const table = screen.getByRole("table", {
    name: /Observed grain yield in kg\/ha/,
  });
  expect(within(table).getAllByRole("row")).toHaveLength(6);
  expect(within(table).getAllByRole("columnheader")).toHaveLength(8);
  expect(within(table).getByText("TZm-1179")).toBeTruthy();
  expect(within(table).getByText("125")).toBeTruthy();
  expect(screen.getByText(/A ratio above 100%/)).toBeTruthy();
  expect(screen.getByText(/Sample size:/)).toBeTruthy();
  expect(screen.getByText(/Not calculated. Choose numbers/)).toBeTruthy();
});

it("exports the preserved report and exposes source audit counts rather than pooled observations", () => {
  const download = vi.fn();
  render(<ScientificReportView report={report} downloadFile={download} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Export scientific report" }),
  );
  expect(download).toHaveBeenCalledWith(
    expect.stringContaining(report.run_id),
    { report },
    "application/json",
  );
  fireEvent.click(
    screen.getByText("Dataset sources, methodology and reproducibility"),
  );
  const inventory = screen.getByRole("table", {
    name: /Source bytes verified/,
  });
  expect(within(inventory).getAllByRole("row")).toHaveLength(11);
  expect(within(inventory).getByText((337913).toLocaleString())).toBeTruthy();
  expect(
    screen.getByText(/must not be summed as independent plots/),
  ).toBeTruthy();
  expect(
    screen
      .getByRole("link", { name: /Penn State STAT 503/ })
      .getAttribute("href"),
  ).toBe("https://online.stat.psu.edu/stat503/Lesson14.html");
});

it("keeps missing evidence and user hypotheses explicit instead of implying completion", () => {
  const altered = structuredClone(report);
  altered.completion_status = "partial";
  const science = altered.scientific_report!;
  science.evidence_coverage = "partial";
  science.missing_tools = ["analyze_trait_associations"];
  science.additional_hypotheses_not_assessed = [
    "<script data-report-fixture>unsafe()</script>",
  ];
  science.candidate_summaries = [];
  science.findings = undefined;
  science.next_experiment = undefined;
  render(<ScientificReportView report={altered} downloadFile={vi.fn()} />);
  expect(screen.getByText(/Unexecuted evidence:/)).toBeTruthy();
  expect(
    screen.getByText("Additional proposals remain unassessed"),
  ).toBeTruthy();
  expect(
    screen.getByText("No complete candidate evidence is available."),
  ).toBeTruthy();
  expect(document.querySelector("script[data-report-fixture]")).toBeNull();
});

it("leaves historical non-profile reports intact", () => {
  const old = { ...report, scientific_report: undefined };
  const { container } = render(
    <ScientificReportView report={old} downloadFile={vi.fn()} />,
  );
  expect(container.textContent).toBe("");
});

it("keeps candidate yield numbers while comparing bars on one shared zero-based scale", () => {
  const { container } = render(
    <ScientificReportView report={report} downloadFile={vi.fn()} />,
  );
  const entries = report.scientific_report!.candidate_summaries!;
  const maximum = Math.max(
    1,
    ...entries.flatMap((entry) => [
      entry.drought_mean_kg_ha ?? 0,
      entry.observed_regime_summary?.well_watered_mean_kg_ha ?? 0,
    ]),
  );
  const bars = container.querySelectorAll<HTMLElement>(
    ".inline-evidence-track > span",
  );
  expect(bars).toHaveLength(entries.length * 2);
  expect(Number.parseFloat(bars[0].style.width)).toBeCloseTo(
    (Number(entries[0].drought_mean_kg_ha) / maximum) * 100,
  );
  expect(bars[0].closest("td")?.textContent).toBe(
    Number(entries[0].drought_mean_kg_ha).toLocaleString(undefined, {
      maximumFractionDigits: 1,
    }),
  );
  expect(screen.getByText(/Yield bars share a zero-based scale/)).toBeTruthy();
});

it("shows the backend observational answer as text alongside the preserved numeric candidate table", () => {
  const current = structuredClone(report);
  current.scientific_report!.observational_answer = {
    summary: "<script data-observational-answer>unsafe()</script> Backend answer fixture; not field validation.",
  };
  render(<ScientificReportView report={current} downloadFile={vi.fn()} />);
  expect(screen.getByText(current.scientific_report!.observational_answer.summary)).toBeTruthy();
  expect(document.querySelector("script[data-observational-answer]")).toBeNull();
  expect(screen.getByRole("table", { name: /Observed grain yield in kg\/ha/ })).toBeTruthy();
});
