import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import fixture from "../fixtures/ghana-ui.json";
import { ResearchTimeline } from "../../app/workspace/ResearchTimeline";
import { WorkspaceErrorItem } from "../../app/workspace/WorkspaceErrorItem";

function TimelineHarness() {
  const [index, setIndex] = useState(0);
  const [presenting, setPresenting] = useState(false);
  return (
    <ResearchTimeline
      events={fixture.events}
      runRetrieving={false}
      runId={fixture.report.run_id}
      runStatus="COMPLETE"
      presenting={presenting}
      setPresenting={setPresenting}
      replayIndex={index}
      setReplayIndex={setIndex}
      replayLoadingId=""
      historyLoading={false}
      historyLoaded={true}
      savedRuns={[]}
      loadHistory={vi.fn()}
      replaySavedRun={vi.fn()}
    />
  );
}

it("keeps keyboard replay selection within the persisted event range", () => {
  render(<TimelineHarness />);
  const slider = screen.getByRole("slider", { name: "Saved event timeline" });
  fireEvent.keyDown(slider, { key: "ArrowRight" });
  expect(slider.getAttribute("aria-valuenow")).toBe("2");
  fireEvent.keyDown(slider, { key: "ArrowDown" });
  expect(slider.getAttribute("aria-valuenow")).toBe("1");
  fireEvent.keyDown(slider, { key: "ArrowLeft" });
  expect(slider.getAttribute("aria-valuenow")).toBe("1");
  fireEvent.keyDown(slider, { key: "End" });
  expect(slider.getAttribute("aria-valuenow")).toBe(
    String(fixture.events.length),
  );
  fireEvent.keyDown(slider, { key: "ArrowUp" });
  expect(slider.getAttribute("aria-valuenow")).toBe(
    String(fixture.events.length),
  );
  fireEvent.keyDown(slider, { key: "Home" });
  expect(slider.getAttribute("aria-valuenow")).toBe("1");
  fireEvent.click(
    screen.getByRole("button", { name: "Replay saved timeline" }),
  );
  expect(
    screen.getByRole("button", { name: "Pause presentation" }),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Pause presentation" }));
  fireEvent.keyDown(slider, { key: "End" });
  fireEvent.click(
    screen.getByRole("button", { name: "Replay saved timeline" }),
  );
  expect(slider.getAttribute("aria-valuenow")).toBe("1");
});

it("routes accessible recovery to the failed resource context", () => {
  const retry = vi.fn();
  const onRetry = vi.fn(
    async (_context: string, operation: () => void | Promise<void>) =>
      operation(),
  );
  render(
    <WorkspaceErrorItem
      context="history"
      details="Fixture network failure"
      copy={{
        title: "History unavailable",
        description: "Retry the saved-run request.",
        action: "Reload history",
        retry,
      }}
      retrying={false}
      onRetry={onRetry}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Reload history" }));
  expect(onRetry).toHaveBeenCalledWith("history", retry);
  expect(retry).toHaveBeenCalledOnce();
});
