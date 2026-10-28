import { useState } from "react";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-ui.json";
import { CinematicPlayer } from "../../app/workspace/CinematicPlayer";
import {
  orderedRunEvents,
  eventTitle,
  eventDescription,
  revealedArtifacts,
  recordedStage,
  cinematicSnapshot,
} from "../../app/workspace/cinematic-model";
import type {
  ResearchArtifact,
  ResearchEvent,
  ResearchReport,
} from "../../app/workspace/workspace-types";

const artifacts = fixture.artifacts as ResearchArtifact[];
const report = fixture.report as ResearchReport;
function Player({
  reduced = false,
  status = "COMPLETE",
  events = fixture.events,
  download = vi.fn(),
}: Readonly<{
  reduced?: boolean;
  status?: string;
  events?: ResearchEvent[];
  download?: (filename: string, value: unknown, mime: string) => void;
}>) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  return (
    <CinematicPlayer
      runId={report.run_id}
      runStatus={status}
      report={report}
      events={events}
      artifacts={artifacts}
      reducedMotion={reduced}
      retrieving={false}
      playing={playing}
      setPlaying={setPlaying}
      index={index}
      setIndex={setIndex}
      downloadFile={download}
    />
  );
}
beforeEach(() => localStorage.removeItem("neurolab-cinematic-rendering"));
afterEach(() => vi.useRealTimers());

it("reveals only evidence already completed at the selected recorded frame, and rewinds honestly", () => {
  const network = vi.spyOn(globalThis, "fetch");
  render(<Player />);
  const evidence = screen.getByRole("region", {
    name: "Evidence revealed at this event",
  });
  expect(within(evidence).queryByText("Observed yield contrast")).toBeNull();
  const slider = screen.getByRole("slider", {
    name: "Cinematic event position",
  });
  fireEvent.keyDown(slider, { key: "End" });
  expect(within(evidence).getByText("Observed yield contrast")).toBeTruthy();
  expect(
    within(evidence).getByText("Leading observed drought means"),
  ).toBeTruthy();
  expect(
    within(evidence).getByRole("img", { name: /95% block-bootstrap interval/ }),
  ).toBeTruthy();
  fireEvent.keyDown(slider, { key: "Home" });
  expect(within(evidence).queryByText("Observed yield contrast")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Next event" }));
  expect(slider.getAttribute("aria-valuenow")).toBe("2");
  expect(network).not.toHaveBeenCalled();
});

it("plays at selected presentation pace, pauses on seek, and stops at the final event", () => {
  vi.useFakeTimers();
  render(<Player />);
  fireEvent.click(screen.getByRole("button", { name: "2×" }));
  fireEvent.click(screen.getByRole("button", { name: "Play replay" }));
  act(() => vi.advanceTimersByTime(900));
  const slider = screen.getByRole("slider", {
    name: "Cinematic event position",
  });
  expect(slider.getAttribute("aria-valuenow")).toBe("2");
  fireEvent.keyDown(slider, { key: "End" });
  expect(screen.getByRole("button", { name: "Play replay" })).toBeTruthy();
  act(() => vi.advanceTimersByTime(5000));
  expect(slider.getAttribute("aria-valuenow")).toBe(
    String(fixture.events.length),
  );
  fireEvent.click(screen.getByRole("button", { name: "Restart" }));
  fireEvent.keyDown(slider, { key: "End" });
  fireEvent.keyDown(slider, { key: "ArrowLeft" });
  fireEvent.click(screen.getByRole("button", { name: "Play replay" }));
  act(() => vi.advanceTimersByTime(900));
  expect(screen.getByRole("button", { name: "Play replay" })).toBeTruthy();
});

it("preserves usable manual playback with reduced motion and no WebGL dependency", () => {
  render(<Player reduced />);
  expect(
    (screen.getByRole("button", { name: "Play replay" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(
    (screen.getByRole("button", { name: "Standard 2D" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Next event" }));
  expect(
    screen
      .getByRole("slider", { name: "Cinematic event position" })
      .getAttribute("aria-valuenow"),
  ).toBe("2");
  expect(screen.getByText(/Reduced motion: use Next event/)).toBeTruthy();
});

it("keeps live mode on the latest persisted event with replay controls disabled", () => {
  render(<Player status="ANALYZING" events={fixture.events.slice(0, 7)} />);
  expect(screen.getByText("RECORDED LIVE EVENTS")).toBeTruthy();
  expect(
    (screen.getByRole("button", { name: "Next event" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(
    screen.getByRole("region", { name: "Evidence revealed at this event" })
      .textContent,
  ).not.toContain("Observed yield contrast");
});

it("exports the unchanged record and opens/closes an accessible immersive dialog", () => {
  const download = vi.fn();
  render(<Player download={download} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Export recorded evidence" }),
  );
  expect(download).toHaveBeenCalledWith(
    expect.stringContaining(report.run_id),
    { report, artifacts, events: fixture.events },
    "application/json",
  );
  fireEvent.click(screen.getByRole("button", { name: /Open cinematic view/ }));
  expect(
    screen.getByRole("dialog", { name: "The evidence, in motion." }),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Close cinematic view" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(
    screen.getByRole("button", { name: /Open cinematic view/ }),
  );
});

it("filters other runs, deduplicates order, withholds mismatched sources, and preserves failure descriptions", () => {
  const first = fixture.events[0];
  const last = fixture.events.at(-1)!;
  expect(
    orderedRunEvents(
      [last, first, first, { ...last, run_id: "other" }],
      report.run_id,
    ),
  ).toEqual([first, last]);
  expect(revealedArtifacts(fixture.events, artifacts, "wrong-source")).toEqual(
    [],
  );
  expect(recordedStage([])).toBe("AWAITING RECORD");
  expect(recordedStage([first])).toBe("RECORDED EVENT");
  expect(eventTitle()).toContain("Waiting");
  expect(eventDescription()).toContain("Choose a saved run");
  const failed = {
    ...last,
    event_type: "run.failed",
    payload: { message: "Actual saved failure" },
  };
  expect(eventTitle(failed)).toBe("Run failed");
  expect(eventDescription(failed)).toBe("Actual saved failure");
  render(<Player events={[]} />);
  expect(
    (
      screen.getByRole("button", {
        name: /Open cinematic view/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});

it("pauses background playback and persists only the optional scene rendering preference", () => {
  vi.useFakeTimers();
  const view = render(<Player />);
  fireEvent.click(screen.getByRole("button", { name: "Standard 2D" }));
  expect(localStorage.getItem("neurolab-cinematic-rendering")).toBe(
    "cinematic",
  );
  expect(
    screen
      .getByRole("button", { name: "Cinematic 3D" })
      .getAttribute("aria-pressed"),
  ).toBe("true");
  fireEvent.click(screen.getByRole("button", { name: "Play replay" }));
  vi.spyOn(document, "hidden", "get").mockReturnValue(true);
  fireEvent(document, new Event("visibilitychange"));
  act(() => vi.advanceTimersByTime(5000));
  expect(
    screen
      .getByRole("slider", { name: "Cinematic event position" })
      .getAttribute("aria-valuenow"),
  ).toBe("1");
  expect(screen.getByRole("button", { name: "Play replay" })).toBeTruthy();
  view.unmount();
  render(<Player reduced />);
  expect(
    (screen.getByRole("button", { name: "Cinematic 3D" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(
    screen.getByRole("img", {
      name: "Illustrative maize plant, leaf and root structure",
    }),
  ).toBeTruthy();
});

it("uses the recorded source during active processing before the final report exists", () => {
  const frame = cinematicSnapshot(
    fixture.events.slice(0, 8),
    report.run_id,
    "ANALYZING",
    0,
    artifacts,
  );
  expect(frame.position).toBe(7);
  expect(frame.revealed.map((artifact) => artifact.tool_name)).toEqual([
    "compare_regimes",
  ]);
  const first = fixture.events[0];
  const malicious = {
    ...first,
    event_type: "tool.completed",
    payload: { artifact_id: {}, sample_size: {} },
  };
  expect(eventDescription(malicious)).not.toContain("[object Object]");
});

it("records worker timeout/failure as terminal without revealing uncompleted evidence", () => {
  const initial = fixture.events[0];
  const terminal = {
    ...initial,
    sequence: 2,
    event_type: "run.timed_out",
    payload: { message: "Execution deadline exceeded." },
  };
  expect(recordedStage([initial, terminal])).toBe("TIMED_OUT");
  expect(
    recordedStage([initial, { ...terminal, event_type: "run.failed" }]),
  ).toBe("FAILED");
  expect(
    revealedArtifacts([initial, terminal], artifacts, report.source_sha256),
  ).toEqual([]);
  expect(eventTitle(terminal)).toBe("Run timed out");
});

it("uses only stored model rationale and keeps recovery outside model attribution", () => {
  const event: ResearchEvent = {
    ...fixture.events[0], event_type: "decision.recorded",
    payload: { selection_source: "model_without_result_feedback",
      model_decision_summary: "Fixture model proposes a coverage audit.",
      decision_summary: "Prior result feedback withheld." },
  };
  expect(eventDescription(event)).toBe(
    "Model-provided rationale (unverified): Fixture model proposes a coverage audit.",
  );
  expect(eventDescription({ ...event, payload: { ...event.payload,
    selection_source: "deterministic_plan_recovery", decision_summary: "Recorded recovery." } })).toBe("Recorded recovery.");
});
