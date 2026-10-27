import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import fixture from "../fixtures/ghana-descriptive-ui.json";
import {
  ExtendedEvidence,
  extendedArtifactsForSection,
} from "../../app/workspace/ExtendedEvidence";
import { CinematicEvidence } from "../../app/workspace/CinematicEvidence";
import type { ResearchArtifact } from "../../app/workspace/workspace-types";
const artifacts = fixture.artifacts as ResearchArtifact[];

it("renders recorded trait associations as an accessible signed matrix with exact units/counts and limits", () => {
  render(<ExtendedEvidence artifacts={[artifacts[0]]} />);
  const table = screen.getByRole("table", {
    name: /Spearman association with grain yield/,
  });
  expect(within(table).getAllByRole("row")).toHaveLength(8);
  expect(within(table).getAllByRole("columnheader")).toHaveLength(7);
  expect(within(table).getAllByText("72")).toHaveLength(7);
  expect(within(table).getByText("asi days")).toBeTruthy();
  expect(within(table).getAllByText("days", { exact: true })).toHaveLength(3);
  expect(screen.getByText(/Seven exploratory traits/)).toBeTruthy();
  expect(screen.queryByText(/No trait-correlation artifact/)).toBeNull();
});

it("shows all saved environment summaries on demand with actual numeric values and no fabricated rank intervals", () => {
  render(<ExtendedEvidence artifacts={[artifacts[1]]} />);
  const tables = screen.getAllByRole("table");
  expect(tables).toHaveLength(2);
  expect(within(tables[0]).getAllByRole("row")).toHaveLength(9);
  fireEvent.click(
    screen.getByRole("button", { name: "Show every environment summary" }),
  );
  expect(within(tables[0]).getAllByRole("row")).toHaveLength(73);
  expect(within(tables[1]).getAllByRole("row")).toHaveLength(73);
  expect(screen.getByText(/not future adaptation/)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Show leading environment summaries" }),
  );
  expect(within(tables[0]).getAllByRole("row")).toHaveLength(9);
});

it("does not convert missing correlation evidence into a zero", () => {
  const altered = structuredClone(artifacts[0]);
  const rows = altered.results.associations as Array<Record<string, unknown>>;
  rows[0].spearman_rho = null;
  rows[0].spearman_rho_95_percentile_interval = null;
  render(<ExtendedEvidence artifacts={[altered]} />);
  expect(screen.getByText("Not estimated")).toBeTruthy();
  expect(screen.getByText("—")).toBeTruthy();
});

it("selects only relevant computed artifacts and exposes them during cinematic playback", () => {
  expect(extendedArtifactsForSection(artifacts, "trait-analytics")).toEqual([
    artifacts[0],
  ]);
  expect(extendedArtifactsForSection(artifacts, "environments")).toEqual([
    artifacts[1],
  ]);
  expect(extendedArtifactsForSection(artifacts, "genotype-explorer")).toEqual(
    [],
  );
  render(<CinematicEvidence artifacts={[artifacts[0]]} />);
  expect(
    screen.getByRole("table", { name: /Spearman association/ }),
  ).toBeTruthy();
  expect(screen.queryByText("Evidence arrives with the record.")).toBeNull();
});
