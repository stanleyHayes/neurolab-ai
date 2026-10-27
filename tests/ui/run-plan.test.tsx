import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ResearchRunPlan } from "../../app/workspace/ResearchRunPlan";
import fixture from "../fixtures/ghana-investigation-ui.json";
import type { ResearchReport } from "../../app/workspace/workspace-types";

it("shows persisted planning ambiguities alongside the exact objective", () => {
  const report = structuredClone(fixture.report) as ResearchReport;
  report.research_plan!.ambiguities = [
    "No focused topic matched; review the selected tasks.",
  ];
  const { container } = render(<ResearchRunPlan report={report} />);
  expect(
    screen.getByText("Planning limits and unresolved questions"),
  ).toBeTruthy();
  expect(
    screen.getByText("No focused topic matched; review the selected tasks."),
  ).toBeTruthy();
  expect(container.querySelector(".objective-verbatim")?.textContent).toBe(
    report.objective,
  );
});

it("groups saved rationale and criteria with the hypothesis without losing the original constraint", async () => {
  const { ResearchHypotheses } =
    await import("../../app/workspace/ResearchHypotheses");
  const hypothesis = "H1: A candidate remains in the observed top quartile.";
  const rationale = "A pooled mean can hide environment-specific variation.";
  const criterion =
    "Require top-quartile ranks in every observed environment. Not validated adaptation.";
  const original = `${hypothesis} Rationale: ${rationale} Criterion: ${criterion}`;
  const { container } = render(
    <ResearchHypotheses
      hypotheses={[hypothesis]}
      constraints={[
        "Retrospective proposals, not a preregistered study.",
        original,
      ]}
    />,
  );
  expect(
    screen.getByRole("heading", {
      name: "A candidate remains in the observed top quartile.",
    }),
  ).toBeTruthy();
  expect(screen.getByText(rationale)).toBeTruthy();
  expect(screen.getByText(criterion)).toBeTruthy();
  expect(
    screen.getByText("Retrospective proposals, not a preregistered study."),
  ).toBeTruthy();
  expect(container.querySelector(".hypothesis-original p")?.textContent).toBe(
    original,
  );
});

it("preserves arbitrary constraints and malformed structured text verbatim", async () => {
  const { ResearchHypotheses } =
    await import("../../app/workspace/ResearchHypotheses");
  const original =
    "H1: Custom hypothesis. Rationale: Keep this text without a criterion delimiter.";
  render(
    <ResearchHypotheses
      hypotheses={["H1: Custom hypothesis."]}
      constraints={[
        original,
        "Do not reinterpret environment indices as calendar years.",
      ]}
    />,
  );
  expect(screen.getByText(original)).toBeTruthy();
  expect(
    screen.getByText(
      "Do not reinterpret environment indices as calendar years.",
    ),
  ).toBeTruthy();
  expect(
    screen.queryByRole("heading", { name: /Evaluation criterion/ }),
  ).toBeNull();
});

it("provides an accessible route to the cinematic replay workspace", () => {
  render(
    <ResearchRunPlan
      report={structuredClone(fixture.report) as ResearchReport}
    />,
  );
  expect(
    screen
      .getByRole("link", { name: "Watch cinematic replay" })
      .getAttribute("href"),
  ).toBe("/live-experiment");
});
