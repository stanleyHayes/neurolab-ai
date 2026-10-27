import type { Dispatch, SetStateAction } from "react";
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
    <article className="card setup-card" id="setup">
      <div className="card-head">
        <span className="eyebrow">NEW EXPERIMENT</span>
        <span className="source-status">SOURCE DATA</span>
      </div>
      <h2>Research brief</h2>
      <ResearchObjectiveEditor
        objective={objective}
        editor={editor}
        busy={busy}
      />
      <div className="setup-meta">
        <span>Ghana · combined field trial</span>
        <span>
          Seed 2026 · {editor.configuration.constraints.max_steps} steps ·{" "}
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
          >
            <span className="choice-indicator" aria-hidden="true" />
            <span className="choice-copy">
              <strong>Deterministic replay</strong>
              <small>Offline baseline · repeatable, no model call</small>
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
          >
            <span className="choice-indicator" aria-hidden="true" />
            <span className="choice-copy">
              <strong>Meta model</strong>
              <small>Requires verified server configuration</small>
            </span>
            <span className="choice-state">
              {mode === "meta" ? "SELECTED" : "GATED"}
            </span>
          </button>
        </fieldset>
      </div>
      <div className="button-row">
        <button
          className="primary-button"
          type="button"
          onClick={() =>
            void runAnalysis(editor.configuration, editor.acceptedPlan)
          }
          disabled={busy || Boolean(editor.validation)}
          aria-busy={busy}
        >
          Generate experiment plan ↗{busy && <LoadingDots />}
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
      <div className="status">{renderedChoice1}</div>
      <div className="notice integrity-notice">
        ◇ Scientific calculations are performed by deterministic tools—not
        invented by the language model.
      </div>
    </article>
  );
}
