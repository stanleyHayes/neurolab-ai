"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { FallbackIllustration } from "../maize-scene-illustration";
import { ResultIcon } from "./ResultIcon";
import { CinematicEvidence } from "./CinematicEvidence";
import {
  eventDescription,
  eventTitle,
  cinematicSnapshot,
  recordedTimestamp,
} from "./cinematic-model";
import type {
  ResearchArtifact,
  ResearchEvent,
  ResearchReport,
} from "./workspace-types";

const MaizeScene = dynamic(() => import("../maize-scene"), {
  ssr: false,
  loading: () => <FallbackIllustration />,
});

type Props = {
  runId: string;
  runStatus: string;
  events: ResearchEvent[];
  artifacts: ResearchArtifact[];
  report: ResearchReport | null;
  reducedMotion: boolean;
  retrieving: boolean;
  playing: boolean;
  setPlaying: Dispatch<SetStateAction<boolean>>;
  index: number;
  setIndex: Dispatch<SetStateAction<number>>;
  downloadFile: (filename: string, value: unknown, mime: string) => void;
};

function TimelineSeek({
  count,
  index,
  seek,
}: Readonly<{ count: number; index: number; seek: (value: number) => void }>) {
  const at = (clientX: number, element: HTMLDivElement) => {
    const bounds = element.getBoundingClientRect();
    if (bounds.width > 0)
      seek(
        Math.round(
          Math.max(0, Math.min(1, (clientX - bounds.left) / bounds.width)) *
            (count - 1),
        ),
      );
  };
  return (
    <div
      className="cinema-seek"
      role="slider"
      tabIndex={count > 1 ? 0 : -1}
      aria-label="Cinematic event position"
      aria-valuemin={1}
      aria-valuemax={Math.max(1, count)}
      aria-valuenow={count ? index + 1 : 1}
      aria-valuetext={
        count ? `Event ${index + 1} of ${count}` : "No recorded events"
      }
      aria-disabled={count < 2}
      onKeyDown={(event) => {
        const keys: Record<string, number> = {
          ArrowRight: index + 1,
          ArrowUp: index + 1,
          ArrowLeft: index - 1,
          ArrowDown: index - 1,
          Home: 0,
          End: count - 1,
        };
        if (event.key in keys && count > 1) {
          event.preventDefault();
          seek(keys[event.key]);
        }
      }}
      onPointerDown={(event) => {
        if (count < 2) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        at(event.clientX, event.currentTarget);
      }}
      onPointerMove={(event) => {
        if (count > 1 && event.currentTarget.hasPointerCapture(event.pointerId))
          at(event.clientX, event.currentTarget);
      }}
    >
      <span className="cinema-seek-rail" />
      <span
        className="cinema-seek-fill"
        style={{ width: `${count > 1 ? (index / (count - 1)) * 100 : 0}%` }}
      />
      <span
        className="cinema-seek-thumb"
        style={{ left: `${count > 1 ? (index / (count - 1)) * 100 : 0}%` }}
      />
    </div>
  );
}

function recordedInference(report: ResearchReport | null): string {
  if (!report) return "Not loaded";
  if (report.mode === "meta")
    return `${report.model_provider ?? "Meta"} · ${report.model_id ?? "model not recorded"}`;
  return "Deterministic tools · no model";
}

export function CinematicPlayer(props: Readonly<Props>) {
  const {
    runId,
    runStatus,
    report,
    artifacts,
    events: rawEvents,
    reducedMotion,
    retrieving,
    playing,
    setPlaying,
    index,
    setIndex,
    downloadFile,
  } = props;
  const [immersive, setImmersive] = useState(false);
  const [cinematic, setCinematic] = useState(
    () =>
      typeof window !== "undefined" &&
      window.localStorage.getItem("neurolab-cinematic-rendering") ===
        "cinematic",
  );
  const [speed, setSpeed] = useState(1);
  const dialog = useRef<HTMLDialogElement>(null);
  const opened = useRef(false);
  const openButton = useRef<HTMLButtonElement>(null);
  const { events, active, position, current, revealed, stage } =
    cinematicSnapshot(
      rawEvents,
      runId,
      runStatus,
      index,
      artifacts,
      report?.source_sha256,
    );
  const canPlay = !active && !retrieving && !reducedMotion && events.length > 1;

  useEffect(() => {
    if (!canPlay || position >= events.length - 1) {
      setPlaying(false);
      return;
    }
    if (!playing) return;
    const timer = window.setTimeout(() => setIndex(position + 1), 1800 / speed);
    return () => window.clearTimeout(timer);
  }, [canPlay, events.length, playing, position, setIndex, setPlaying, speed]);
  useEffect(() => {
    if (immersive && !dialog.current?.open) {
      opened.current = true;
      dialog.current?.showModal();
    } else if (!immersive && opened.current) {
      opened.current = false;
      openButton.current?.focus();
    }
  }, [immersive]);
  useEffect(() => {
    const pause = () => {
      if (document.hidden) setPlaying(false);
    };
    document.addEventListener("visibilitychange", pause);
    return () => document.removeEventListener("visibilitychange", pause);
  }, [setPlaying]);

  const seek = (value: number) => {
    setPlaying(false);
    setIndex(Math.max(0, Math.min(events.length - 1, value)));
  };
  const close = () => {
    setPlaying(false);
    if (dialog.current?.open) dialog.current.close();
    setImmersive(false);
  };
  const toggleRendering = () => {
    const next = !cinematic;
    setCinematic(next);
    window.localStorage.setItem(
      "neurolab-cinematic-rendering",
      next ? "cinematic" : "standard",
    );
  };
  const content = (
    <>
      <header className="cinema-header">
        <div>
          <span className="cinema-kicker">
            <ResultIcon name="evidence" />{" "}
            {active ? "RECORDED LIVE EVENTS" : "REPLAY · SAVED RESEARCH"}
          </span>
          <h2 id={immersive ? "cinema-dialog-title" : "cinema-inline-title"}>
            The evidence, in motion.
          </h2>
          <p>
            {active
              ? "Following persisted backend events. No estimated progress."
              : "Presentation of an existing run. No new analysis or Meta call."}
          </p>
        </div>
        {immersive ? (
          <button type="button" className="secondary-button" onClick={close}>
            Close cinematic view
          </button>
        ) : (
          <button
            ref={openButton}
            type="button"
            className="secondary-button"
            onClick={() => setImmersive(true)}
            disabled={!events.length}
          >
            Open cinematic view ↗
          </button>
        )}
      </header>
      <output className="sr-only">Recorded stage: {stage}</output>
      <div className="cinema-layout">
        <aside className="cinema-brief" aria-label="Recorded research context">
          <span className="cinema-panel-label">
            <ResultIcon name="record" /> THE RESEARCH QUESTION
          </span>
          <p className="cinema-objective">
            {report?.objective ??
              "Load a saved run to inspect its original research question."}
          </p>
          <dl>
            <div>
              <dt>Run</dt>
              <dd>{runId.slice(0, 8) || "None selected"}</dd>
            </div>
            <div>
              <dt>Dataset</dt>
              <dd>{report?.dataset_id ?? "Not recorded"}</dd>
            </div>
            <div>
              <dt>Seed</dt>
              <dd>{report?.seed ?? "Not recorded"}</dd>
            </div>
            <div>
              <dt>Recorded inference</dt>
              <dd>{recordedInference(report)}</dd>
            </div>
          </dl>
          <details>
            <summary>Source &amp; scientific limits</summary>
            <code>{report?.source_sha256 ?? "Source not loaded"}</code>
            <a
              href="https://doi.org/10.5281/zenodo.22666201"
              target="_blank"
              rel="noreferrer"
            >
              Ghana source · Abu et al. (2026) ↗
            </a>
            <p>
              Observed Ghana field records. Water regime and environment are
              confounded. ENVT indices are not calendar years.
            </p>
            {report?.limitations.map((limit) => (
              <p key={limit}>{limit}</p>
            ))}
          </details>
          <div className="cinema-trust-note">
            <ResultIcon name="caution" />
            <p>
              Exploratory evidence. Playback is not a crop simulation or a new
              scientific discovery.
            </p>
          </div>
          <button
            className="text-button"
            type="button"
            disabled={!report}
            onClick={() =>
              downloadFile(
                `neurolab-${runId}-replay.json`,
                { report, artifacts, events },
                "application/json",
              )
            }
          >
            <ResultIcon name="download" /> Export recorded evidence
          </button>
        </aside>
        <div className="cinema-center">
          <section
            className="cinema-stage"
            aria-label="Recorded processing stage"
          >
            <div className="cinema-stage-top">
              <span>{stage.replaceAll("_", " ")}</span>
              <span>
                {active ? "EVENT STREAM" : "SAVED FRAME"}{" "}
                {events.length ? position + 1 : 0} / {events.length}
              </span>
            </div>
            <div
              className="cinema-plant"
              aria-label="Illustrative maize plant, not measured morphology"
            >
              {cinematic && !reducedMotion ? (
                <MaizeScene reducedMotion={false} />
              ) : (
                <FallbackIllustration />
              )}
              <span className="cinema-plant-label">
                ILLUSTRATIVE PLANT MODEL · NO SIMULATED MEASUREMENTS
              </span>
            </div>
            <div className="cinema-current" key={current?.event_id ?? "empty"}>
              <span className="cinema-panel-label">
                {recordedTimestamp(current)}
              </span>
              <h3>{eventTitle(current)}</h3>
              <p>{eventDescription(current)}</p>
            </div>
            <div className="cinema-render-choice">
              <span>Scene rendering</span>
              <button
                type="button"
                className="text-button"
                onClick={toggleRendering}
                aria-pressed={cinematic}
                disabled={reducedMotion}
              >
                {cinematic ? "Cinematic 3D" : "Standard 2D"}
              </button>
            </div>
          </section>
          <CinematicEvidence artifacts={revealed} />
        </div>
        <aside className="cinema-events" aria-label="Recorded event chapters">
          <span className="cinema-panel-label">
            <ResultIcon name="retention" /> PROCESSING RECORD
          </span>
          <p className="caption">
            Select any recorded event to inspect that frame.
          </p>
          <ol>
            {events.map((event, eventIndex) => (
              <li key={event.event_id}>
                <button
                  type="button"
                  onClick={() => seek(eventIndex)}
                  disabled={active || retrieving}
                  aria-current={eventIndex === position ? "step" : undefined}
                >
                  <span className="cinema-event-number">
                    {String(eventIndex + 1).padStart(2, "0")}
                  </span>
                  <span>
                    <strong>{eventTitle(event)}</strong>
                    <small>
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </small>
                  </span>
                  {eventIndex < position && <ResultIcon name="complete" />}
                </button>
              </li>
            ))}
          </ol>
          {!events.length && (
            <p>No saved events yet. Choose a run from the history below.</p>
          )}
        </aside>
      </div>
      <footer className="cinema-controls">
        <div className="cinema-transport">
          <button
            className="secondary-button"
            type="button"
            onClick={() => seek(0)}
            disabled={active || !events.length}
          >
            Restart
          </button>
          <button
            className="primary-button"
            type="button"
            disabled={!canPlay}
            onClick={() => {
              if (position === events.length - 1) setIndex(0);
              setPlaying((value) => !value);
            }}
          >
            {playing ? "Pause replay" : "Play replay"}
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={
              active ||
              retrieving ||
              !events.length ||
              position >= events.length - 1
            }
            onClick={() => seek(position + 1)}
          >
            Next event
          </button>
        </div>
        <TimelineSeek
          count={active ? 0 : events.length}
          index={position}
          seek={seek}
        />
        <fieldset className="cinema-speed">
          <legend>Playback pace</legend>
          {[1, 2, 4].map((value) => (
            <button
              className="text-button"
              type="button"
              key={value}
              aria-pressed={speed === value}
              onClick={() => setSpeed(value)}
            >
              {value}×
            </button>
          ))}
        </fieldset>
        <p>
          {reducedMotion
            ? "Reduced motion: use Next event or the event chapters; autoplay and 3D are off."
            : "Readable pacing: 1.8 seconds per event at 1×. Recorded timestamps remain unchanged."}
        </p>
      </footer>
    </>
  );
  return (
    <>
      <article
        className={`cinema-player${reducedMotion ? " cinema-reduced" : ""}`}
        aria-label="Cinematic research replay"
        aria-busy={retrieving}
      >
        {!immersive && content}
      </article>
      <dialog
        ref={dialog}
        className={`cinema-dialog${reducedMotion ? " cinema-reduced" : ""}`}
        aria-labelledby="cinema-dialog-title"
        onCancel={close}
        onClose={close}
      >
        {immersive && content}
      </dialog>
    </>
  );
}
