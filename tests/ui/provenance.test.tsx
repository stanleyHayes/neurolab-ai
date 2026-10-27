import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-ui.json";
import { SourceProvenance } from "../../app/workspace/SourceProvenance";
import type { ResearchReport } from "../../app/workspace/workspace-types";
const report = fixture.report as ResearchReport;

it("presents actual dataset counts and citation with visible scientific limitations", () => {
  render(
    <SourceProvenance
      profile={fixture.profile}
      profileLoading={false}
      report={report}
    />,
  );
  expect(screen.getAllByRole("definition")).toHaveLength(3);
  const counts = screen.getByRole("list", { name: "" });
  expect(within(counts).getByText("Managed drought")).toBeTruthy();
  expect(
    screen
      .getByRole("link", { name: /Abu et al. \(2026\)/ })
      .getAttribute("href"),
  ).toBe("https://doi.org/10.5281/zenodo.22666201");
  expect(screen.getByText(String(fixture.profile.row_count))).toBeTruthy();
  expect(screen.getByText(String(fixture.profile.genotype_count))).toBeTruthy();
  expect(screen.getByText("Selected run matches this source")).toBeTruthy();
  expect(
    screen.getByText(/Water regime is confounded with trial environment/),
  ).toBeTruthy();
  expect(screen.getByText(fixture.profile.source_sha256)).toBeTruthy();
});

it("copies the exact immutable source identity and handles unavailable clipboard support", async () => {
  const copy = vi.fn(async () => undefined);
  vi.stubGlobal("navigator", { clipboard: { writeText: copy } });
  render(
    <SourceProvenance
      profile={fixture.profile}
      profileLoading={false}
      report={null}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Copy source hash" }));
  await screen.findByText("Source hash copied.");
  expect(copy).toHaveBeenCalledWith(fixture.profile.source_sha256);
  copy.mockRejectedValueOnce(new Error("Clipboard unavailable"));
  fireEvent.click(screen.getByRole("button", { name: "Copy source hash" }));
  await screen.findByText(/Copy is unavailable/);
});

it("identifies mismatched run sources without presenting them as matched evidence", () => {
  const different = { ...report, source_sha256: "f".repeat(64) };
  render(
    <SourceProvenance
      profile={fixture.profile}
      profileLoading={false}
      report={different}
    />,
  );
  expect(screen.getByText("Selected run uses a different source")).toBeTruthy();
  expect(screen.getByText(different.source_sha256)).toBeTruthy();
  expect(screen.queryByText("Selected run matches this source")).toBeNull();
});

it("does not invent counts or a match when the current source is unavailable", async () => {
  const view = render(
    <SourceProvenance profile={null} profileLoading={true} report={null} />,
  );
  expect(
    (
      screen.getByRole("button", {
        name: "Copy source hash",
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  view.rerender(
    <SourceProvenance profile={null} profileLoading={false} report={report} />,
  );
  expect(screen.getByText("SOURCE UNAVAILABLE")).toBeTruthy();
  expect(
    screen.getByText("Run source recorded; current source unavailable"),
  ).toBeTruthy();
  await waitFor(() => expect(screen.getAllByText("—")).toHaveLength(3));
});
