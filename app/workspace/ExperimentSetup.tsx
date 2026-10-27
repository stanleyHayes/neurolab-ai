import { useEffect, type Dispatch, type SetStateAction } from "react";
import Link from "next/link";
import { ResultIcon } from "./ResultIcon";
import { useInferenceAvailability } from "./use-inference-availability";
import { LoadingDots } from "./LoadingDots";
import { useResearchEditor } from "./use-research-editor";
import { ResearchObjectiveEditor } from "./ResearchObjectiveEditor";
import type {
  ResearchConfiguration,
  ResearchPlan,
} from "./research-editor-types";

type ExperimentSetupProps = {
  objective: string;
  setObjective: Dispatch<SetStateAction<string>>;
  mode: "replay" | "meta";
  setMode: Dispatch<SetStateAction<"replay" | "meta">>;
  busy: boolean;
  canceling: boolean;
  runId: string;
  runStatus: string;
  toolCalls?: number;
  runAnalysis: (
    configuration?: ResearchConfiguration,
    plan?: ResearchPlan | null,
  ) => Promise<void>;
  cancelRun: () => Promise<void>;
};

export function ExperimentSetup({
  objective,
  setObjective,
  mode,
  setMode,
  busy,
  canceling,
  runId,
  runStatus,
  toolCalls,
  runAnalysis,
  cancelRun,
}: Readonly<ExperimentSetupProps>) {
  const editor = useResearchEditor(objective, setObjective);
  const inference = useInferenceAvailability();
  useEffect(() => {
    if (!inference.checking && !inference.enabled && mode === "meta")
      setMode("replay");
  }, [inference.checking, inference.enabled, mode, setMode]);
  const toolCountLabel =
    toolCalls === undefined ? "" : " · " + toolCalls + " tool calls";
  const renderedChoice1 = (() => {
    if (busy) {
      return `Run ${runId.slice(0, 8) || "queued"} · ${runStatus || "starting"}`;
    }
    if (runStatus) {
      return `Run ${runStatus.toLowerCase()}${toolCountLabel}`;
    }
    return "Ready · all run state comes from durable backend events";
  })();
  return (
    <article className="card setup-card setup-workbench" id="setup">
      <div className="card-head">
        <span className="eyebrow">NEW EXPERIMENT</span>
        <span className="source-status">SOURCE DATA</span>
      </div>
      <header className="setup-intro">
        <h2>Shape the next investigation.</h2>
        <p>Start with a question. Keep the evidence traceable.</p>
      </header>
      <ResearchObjectiveEditor
        objective={objective}
        editor={editor}
        busy={busy}
        inferenceAvailable={inference.enabled}
      />
      <div className="setup-meta">
        <span>
          <ResultIcon name="plots" /> Ghana · combined field trial
        </span>
        <span>
          <ResultIcon name="method" /> Seed 2026 ·{" "}
          {editor.configuration.constraints.max_steps} steps ·{" "}
          {editor.configuration.constraints.max_tool_calls} calls ·{" "}
          {editor.configuration.constraints.max_seconds} s
        </span>
      </div>
      <div className="planner-field" id="settings">
        <span className="field-label" id="analysis-planner-label">
          Analysis mode
        </span>
        <fieldset
          className="planner-options"

          aria-labelledby="analysis-planner-label"
        >
          <button
            className={`planner-choice${mode === "replay" ? " selected" : ""}`}
            type="button"
            aria-pressed={mode === "replay"}
            onClick={() => setMode("replay")}
            disabled={busy}
          >
            <span className="setup-mode-icon">
              <ResultIcon name="retention" />
            </span>
            <span className="choice-copy">
              <strong>Deterministic analysis</strong>
              <small>Real data · repeatable tools · no Meta credits</small>
            </span>
            <span className="choice-state">
              {mode === "replay" ? "SELECTED" : "AVAILABLE"}
            </span>
          </button>
          <button
            className={`planner-choice${mode === "meta" ? " selected" : ""}`}
            type="button"
            aria-pressed={mode === "meta"}
            onClick={() => setMode("meta")}
            disabled={!inference.enabled || busy}
          >
            <span className="setup-mode-icon">
              <ResultIcon name="spark" />
            </span>
            <span className="choice-copy">
              <strong>Meta-assisted research</strong>
              <small>Structured planning with a verified live model</small>
            </span>
            <span className="choice-state">
              {inference.enabled ? "AVAILABLE" : "PAUSED"}
            </span>
          </button>
        </fieldset>
      </div>
      <div className="setup-inference-note">
        <ResultIcon name={inference.enabled ? "complete" : "caution"} />
        <span>{inference.reason}</span>
      </div>
      <div className="setup-launch-row">
        <div>
          <span className="eyebrow">READY WHEN YOU ARE</span>
          <p>Run the supported tools on the original field records.</p>
        </div>
        <div className="button-row">
          <button
            className="primary-button"
            type="button"
            onClick={() =>
              void runAnalysis(editor.configuration, editor.acceptedPlan)
            }
            disabled={
              busy ||
              Boolean(editor.validation) ||
              (mode === "meta" && !inference.enabled)
            }
            aria-busy={busy}
            aria-label="Generate experiment plan"
          >
            Start investigation <ResultIcon name="arrow" />
            {busy && <LoadingDots />}
          </button>
          {busy && (
            <button
              className="secondary-button"
              type="button"
              onClick={() => void cancelRun()}
              disabled={canceling}
              aria-busy={canceling}
            >
              Request cancellation{canceling && <LoadingDots />}
            </button>
          )}
        </div>
      </div>
      <div className="status">{renderedChoice1}</div>
      <div className="setup-integrity">
        <ResultIcon name="source" />
        <p>
          Numeric tools calculate the results. Every finding stays linked to its
          source and recorded analysis.
        </p>
        <Link href="/live-experiment">
          Replay saved results <ResultIcon name="arrow" />
        </Link>
      </div>
    </article>
  );
}
