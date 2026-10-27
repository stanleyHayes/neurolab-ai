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
