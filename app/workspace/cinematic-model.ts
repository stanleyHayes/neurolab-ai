import type { ResearchArtifact, ResearchEvent } from "./workspace-types";
import { EVENT_LABELS } from "./workspace-config";

export function orderedRunEvents(events: ResearchEvent[], runId: string) {
  const unique = new Map<number, ResearchEvent>();
  for (const event of events) {
    if (event.run_id === runId && Number.isInteger(event.sequence))
      unique.set(event.sequence, event);
  }
  return [...unique.values()].sort((a, b) => a.sequence - b.sequence);
}

export function eventTitle(event?: ResearchEvent): string {
  if (!event) return "Waiting for recorded events";
  if (
    event.event_type === "stage.changed" &&
    typeof event.payload.stage === "string"
  )
    return event.payload.stage.replaceAll("_", " ");
  return EVENT_LABELS[event.event_type] ?? event.event_type;
}

function displayValue(value: unknown, fallback: string): string {
  return typeof value === "string" || typeof value === "number"
    ? `${value}`
    : fallback;
}

export function modelRationale(event: ResearchEvent): string | null {
  if (
    event.event_type === "decision.recorded" &&
    ["model", "model_without_result_feedback"].includes(
      String(event.payload.selection_source),
    ) &&
    typeof event.payload.model_decision_summary === "string" &&
    event.payload.model_decision_summary.trim()
  )
    return `Model-provided rationale (unverified): ${event.payload.model_decision_summary}`;
  return null;
}

export function eventDescription(event?: ResearchEvent): string {
  if (!event)
    return "Choose a saved run below to replay its actual processing history.";
  const rationale = modelRationale(event);
  if (rationale) return rationale;
  for (const key of [
    "public_summary",
    "decision_summary",
    "summary",
    "label",
    "message",
  ])
    if (typeof event.payload[key] === "string") return event.payload[key];
  if (event.event_type === "tool.completed")
    return `Recorded artifact ${displayValue(event.payload.artifact_id, "unavailable")}; ${displayValue(event.payload.sample_size, "unknown")} observed records.`;
  if (typeof event.payload.action === "string")
    return `Allowlisted analysis: ${event.payload.action}`;
  return "Persisted backend event. No computation is performed by this playback.";
}

export function revealedArtifacts(
  events: ResearchEvent[],
  artifacts: ResearchArtifact[],
  sourceHash?: string,
) {
  const completed = new Set(
    events
      .filter((event) => event.event_type === "tool.completed")
      .map((event) => event.payload.artifact_id),
  );
  return artifacts.filter(
    (artifact) =>
      completed.has(artifact.artifact_id) &&
      artifact.source_sha256 === sourceHash,
  );
}

export function recordedStage(events: ResearchEvent[]): string {
  for (const event of [...events].reverse()) {
    const terminal: Record<string, string> = {
      "run.completed": "COMPLETE",
      "run.partial": "PARTIAL",
      "run.failed": "FAILED",
      "run.cancelled": "CANCELLED",
      "run.timed_out": "TIMED_OUT",
    };
    if (terminal[event.event_type]) return terminal[event.event_type];
    if (
      event.event_type === "stage.changed" &&
      typeof event.payload.stage === "string"
    )
      return event.payload.stage;
  }
  return events.length ? "RECORDED EVENT" : "AWAITING RECORD";
}

export function cinematicSnapshot(
  rawEvents: ResearchEvent[],
  runId: string,
  runStatus: string,
  index: number,
  artifacts: ResearchArtifact[],
  sourceHash?: string,
) {
  const events = orderedRunEvents(rawEvents, runId);
  const active = [
    "CREATED",
    "VALIDATING",
    "PLANNING",
    "QUEUED",
    "RUNNING",
    "ANALYZING",
    "CANCEL_REQUESTED",
  ].includes(runStatus);
  const position = active
    ? Math.max(0, events.length - 1)
    : Math.max(0, Math.min(index, events.length - 1));
  const visibleEvents = events.slice(0, position + 1);
  const recordedHash = events.find(
    (event) => event.event_type === "run.created",
  )?.payload.source_sha256;
  const hash =
    sourceHash ?? (typeof recordedHash === "string" ? recordedHash : undefined);
  return {
    events,
    active,
    position,
    current: events[position],
    revealed: revealedArtifacts(visibleEvents, artifacts, hash),
    stage: recordedStage(visibleEvents),
  };
}

export function recordedTimestamp(event?: ResearchEvent): string {
  return event
    ? new Date(event.timestamp).toLocaleString()
    : "NO RECORDED TIMESTAMP";
}
