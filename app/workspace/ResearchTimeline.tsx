"use client";

import Link from "next/link";
import type { Dispatch, SetStateAction } from "react";
import { EmptyState } from "./EmptyState";
import { LoadingDots } from "./LoadingDots";
import { Skeleton } from "./Skeleton";
import { EVENT_LABELS } from "./workspace-config";
import type { ResearchEvent, SavedRun } from "./workspace-types";

type ResearchTimelineProps = {
  events: ResearchEvent[];
  runRetrieving: boolean;
  runId: string;
  runStatus: string;
  presenting: boolean;
  setPresenting: Dispatch<SetStateAction<boolean>>;
  replayIndex: number;
  setReplayIndex: Dispatch<SetStateAction<number>>;
  replayLoadingId: string;
  historyLoading: boolean;
  historyLoaded: boolean;
  historyError?: string;
  savedRuns: SavedRun[];
  loadHistory: () => Promise<void>;
  replaySavedRun: (id: string) => Promise<void>;
};

function displayText(value: unknown, fallback = "—"): string {
  return typeof value === "string" ? value : fallback;
}

function eventSummary(event: ResearchEvent): string {
  const payload = event.payload ?? {};
  if (event.event_type === "stage.changed")
    return displayText(payload.public_summary);
  if (event.event_type === "tool.completed")
    return `${displayText(payload.artifact_id)} · n=${displayText(payload.sample_size)}`;
  if (event.event_type === "tool.requested")
    return `Allowlisted tool · ${displayText(payload.action)}`;
  if (event.event_type === "decision.recorded")
    return `${displayText(payload.selected_action)} · ${displayText(payload.decision_summary)}`;
  if (event.event_type === "tool.failed" || event.event_type === "run.failed") {
    return `${displayText(payload.error_type, "Error")} · ${displayText(payload.message, "See run error details")}`;
  }
  if (event.event_type === "run.created")
    return `Dataset · ${displayText(payload.dataset_id)}`;
  return displayText(
    payload.label,
    displayText(payload.summary, "Persisted state transition"),
  );
}

export function ResearchTimeline(props: Readonly<ResearchTimelineProps>) {
  const {
    events,
    runRetrieving,
    runId,
    runStatus,
    presenting,
    setPresenting,
    replayIndex,
    setReplayIndex,
    replayLoadingId,
    historyLoading,
    historyLoaded,
    historyError,
    savedRuns,
    loadHistory,
    replaySavedRun,
  } = props;
  const currentEvent =
    events[Math.min(replayIndex, Math.max(0, events.length - 1))];
  const selectedEventNumber = Math.min(replayIndex + 1, events.length);
  const selectFromPointer = (clientX: number, element: HTMLDivElement) => {
    const bounds = element.getBoundingClientRect();
    setReplayIndex(
      Math.round(
        Math.max(0, Math.min(1, (clientX - bounds.left) / bounds.width)) *
          (events.length - 1),
      ),
    );
  };

  const renderedChoice1 = (() => {
    if (events.length) {
      return events.map((event) => (
        <li className="event" key={event.event_id}>
          <span className="event-sequence">
            {String(event.sequence).padStart(2, "0")}
          </span>
          <div>
            <strong>
              {EVENT_LABELS[event.event_type] ?? event.event_type}
            </strong>
            <p>{eventSummary(event)}</p>
            <time dateTime={event.timestamp}>
              {new Date(event.timestamp).toLocaleTimeString()}
            </time>
          </div>
        </li>
      ));
    }
    if (runRetrieving) {
      return (
        <li className="event-retrieval-skeleton" aria-hidden="true">
          <Skeleton className="skeleton-event-index" />
          <span>
            <Skeleton className="skeleton-line" />
            <Skeleton className="skeleton-line skeleton-line-short" />
          </span>
        </li>
      );
    }
    return (
      <li className="empty-state-list-item">
        <EmptyState
          compact
          icon="events"
          title="No saved events yet"
          description="Run events appear here after the backend records them. Nothing is simulated."
          action={
            <Link className="text-link" href="/experiment-studio">
              Start an experiment ↗
            </Link>
          }
        />
      </li>
    );
  })();
  const renderedChoice2 = (() => {
    if (savedRuns.length) {
      return savedRuns.map((saved) => (
        <li key={saved.run_id}>
          <button
            type="button"
            className="history-item"
            onClick={() => void replaySavedRun(saved.run_id)}
            disabled={Boolean(replayLoadingId)}
            aria-busy={replayLoadingId === saved.run_id}
          >
            <span>
              <strong>{saved.objective}</strong>
              <small>
                {new Date(saved.created_at).toLocaleString()} · {saved.status}
              </small>
            </span>
            <span className="history-item-action">
              {replayLoadingId === saved.run_id ? (
                <LoadingDots />
              ) : (
                <span aria-hidden="true">↗</span>
              )}
            </span>
          </button>
        </li>
      ));
    }
    if (historyLoading) {
      return (
        <li className="history-skeleton-list">
          <output aria-label="Loading saved runs">
            <span className="sr-only">Loading saved runs</span>
            {[0, 1, 2].map((index) => (
              <span
                className="history-skeleton-row"
                aria-hidden="true"
                key={index}
              >
                <Skeleton className="skeleton-line" />
                <Skeleton className="skeleton-line skeleton-line-short" />
              </span>
            ))}
          </output>
        </li>
      );
    }
    if (historyLoaded && !historyError) {
      return (
        <li className="empty-state-list-item">
          <EmptyState
            compact
            icon="archive"
            title="No saved runs yet"
            description="Completed runs are kept here so you can reopen their evidence."
            action={
              <Link className="text-link" href="/experiment-studio">
                Create a research run ↗
              </Link>
            }
          />
        </li>
      );
    }
    return null;
  })();
  return (
    <article className="card timeline-card" id="timeline">
      <div className="card-head">
        <span className="eyebrow">LIVE EXPERIMENT</span>
      </div>
      <h2>Research timeline &amp; saved runs</h2>
      {runRetrieving && (
        <output className="experiment-retrieval" aria-live="polite">
          <span className="retrieval-signal" aria-hidden="true" />
          <span className="retrieval-copy">
            <strong>Retrieving persisted experiment results</strong>
            <span className="retrieval-description">
              Loading saved events and artifacts for run {runId.slice(0, 8)}.
              Results appear when retrieved.
            </span>
          </span>
        </output>
      )}
      <div className="stage-strip" aria-label="Current research stage">
        {["CREATED", "PLANNING", "QUEUED", "ANALYZING", "COMPLETE"].map(
          (stage) => (
            <span
              className={runStatus === stage ? "stage active" : "stage"}
              key={stage}
            >
              {stage}
            </span>
          ),
        )}
      </div>
      <ol
        className="event-list"
        aria-label="Persisted research events"
        aria-busy={runRetrieving}
      >
        {renderedChoice1}
      </ol>
      {events.length > 0 && (
        <div className="presentation-controls">
          <button
            className="secondary-button"
            type="button"
            onClick={() => setPresenting((value) => !value)}
            disabled={Boolean(replayLoadingId)}
            aria-busy={Boolean(replayLoadingId)}
          >
            {presenting ? "Pause presentation" : "Replay saved timeline"}
            {replayLoadingId && <LoadingDots />}
          </button>
          <span className="replay-position" aria-hidden="true">
            EVENT{" "}
            <strong>{selectedEventNumber.toString().padStart(2, "0")}</strong> /{" "}
            {events.length.toString().padStart(2, "0")}
          </span>
          <div
            className={`replay-scrubber${events.length < 2 ? " disabled" : ""}`}
            role="slider"
            tabIndex={events.length < 2 ? -1 : 0}
            aria-label="Saved event timeline"
            aria-orientation="horizontal"
            aria-valuemin={1}
            aria-valuemax={events.length}
            aria-valuenow={selectedEventNumber}
            aria-valuetext={`Event ${selectedEventNumber} of ${events.length}: ${EVENT_LABELS[currentEvent?.event_type ?? ""] ?? currentEvent?.event_type ?? "No event"}`}
            aria-disabled={events.length < 2}
            onKeyDown={(event) => {
              if (events.length < 2) return;
              if (event.key === "ArrowRight" || event.key === "ArrowUp") {
                event.preventDefault();
                setReplayIndex((index) =>
                  Math.min(events.length - 1, index + 1),
                );
              } else if (
                event.key === "ArrowLeft" ||
                event.key === "ArrowDown"
              ) {
                event.preventDefault();
                setReplayIndex((index) => Math.max(0, index - 1));
              } else if (event.key === "Home") {
                event.preventDefault();
                setReplayIndex(0);
              } else if (event.key === "End") {
                event.preventDefault();
                setReplayIndex(events.length - 1);
              }
            }}
            onPointerDown={(event) => {
              if (events.length < 2) return;
              event.currentTarget.setPointerCapture(event.pointerId);
              selectFromPointer(event.clientX, event.currentTarget);
            }}
            onPointerMove={(event) => {
              if (
                events.length < 2 ||
                !event.currentTarget.hasPointerCapture(event.pointerId)
              )
                return;
              selectFromPointer(event.clientX, event.currentTarget);
            }}
          >
            <span className="scrubber-rail" aria-hidden="true">
              <span
                className="scrubber-progress"
                style={{
                  width: `${events.length > 1 ? (replayIndex / (events.length - 1)) * 100 : 0}%`,
                }}
              />
            </span>
            <span
              className="scrubber-thumb"
              aria-hidden="true"
              style={{
                left: `${events.length > 1 ? (replayIndex / (events.length - 1)) * 100 : 0}%`,
              }}
            />
          </div>
        </div>
      )}
      {currentEvent && (
        <div className="current-stage" aria-live="polite">
          <span>REPLAY FRAME</span>
          <strong>
            {EVENT_LABELS[currentEvent.event_type] ?? currentEvent.event_type}
          </strong>
          <p>
            {displayText(
              currentEvent.payload.public_summary,
              displayText(
                currentEvent.payload.decision_summary,
                currentEvent.event_type,
              ),
            )}
          </p>
        </div>
      )}
      <div className="history-heading">
        <h3>Saved runs</h3>
        <button
          className="text-button"
          type="button"
          onClick={() => void loadHistory()}
          disabled={historyLoading}
          aria-busy={historyLoading}
        >
          Refresh{historyLoading && <LoadingDots />}
        </button>
      </div>
      <ul className="history-list" aria-busy={historyLoading}>
        {renderedChoice2}
      </ul>
    </article>
  );
}
