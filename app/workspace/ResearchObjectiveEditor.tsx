"use client";
import { useEffect, useRef, useState } from "react";
import { OBJECTIVE_LIMIT } from "./research-editor-types";
import { ResultIcon } from "./ResultIcon";
import { LoadingDots } from "./LoadingDots";
import { ResearchConfigurationPanel } from "./ResearchConfigurationPanel";
import { AcceptedResearchPlan, ResearchPlanReview } from "./ResearchPlanReview";
import type { ResearchEditorState } from "./use-research-editor";

type Props = {
  objective: string;
  editor: ResearchEditorState;
  busy: boolean;
  inferenceAvailable?: boolean;
};
export function ResearchObjectiveEditor({
  objective,
  editor,
  busy,
  inferenceAvailable = true,
}: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const expandedInput = useRef<HTMLTextAreaElement>(null);
  const expandButton = useRef<HTMLButtonElement>(null);
  const count = Array.from(objective).length;
  useEffect(() => {
    if (expanded) {
      dialog.current?.showModal();
      expandedInput.current?.focus();
    } else dialog.current?.close();
  }, [expanded]);
  const close = () => {
    setExpanded(false);
    expandButton.current?.focus();
  };
  const editorCounter = `${count.toLocaleString()} / ${OBJECTIVE_LIMIT.toLocaleString()} characters`;
  return (
    <div className="research-objective-editor">
      <div className="objective-heading">
        <label htmlFor="objective">Research question</label>
        <button
          className="text-button"
          type="button"
          ref={expandButton}
          onClick={() => setExpanded(true)}
        >
          Expand writing space ↗
        </button>
      </div>
      <p id="objective-help" className="caption">
        Outline your question, hypotheses and constraints. Your complete brief
        and paragraph breaks stay intact.
      </p>
      <textarea
        id="objective"
        value={objective}
        rows={10}
        onChange={(event) => editor.changeObjective(event.target.value)}
        aria-describedby="objective-help objective-counter objective-validation"
        aria-invalid={count > OBJECTIVE_LIMIT}
        disabled={busy}
        spellCheck={false}
      />
      <div className="editor-meta">
        <span
          id="objective-counter"
          className={count > OBJECTIVE_LIMIT ? "warning" : ""}
        >
          {editorCounter}
        </span>
        <span>
          {editor.dirty ? "Unsaved changes" : "Account draft"} · revision{" "}
          {editor.revision}
        </span>
      </div>
      <p
        id="objective-validation"
        className="editor-validation"
        aria-live="polite"
      >
        {editor.validation}
      </p>
      <div className="editor-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={
            busy ||
            editor.saving ||
            editor.loading ||
            Boolean(editor.validation)
          }
          onClick={() => void editor.saveDraft()}
          aria-busy={editor.saving}
        >
          <ResultIcon name="save" /> Save draft
          {editor.saving && <LoadingDots />}
        </button>
        <button
          className="text-button"
          type="button"
          disabled={busy || editor.loading || editor.saving}
          onClick={() => void editor.loadDraft()}
          aria-busy={editor.loading}
        >
          <ResultIcon name="source" /> Load saved draft
          {editor.loading && <LoadingDots />}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={
            busy ||
            editor.refining ||
            Boolean(editor.validation) ||
            !inferenceAvailable ||
            editor.configuration.desired_outputs.includes(
              "ghana_drought_investigation",
            )
          }
          onClick={() => void editor.refine()}
          aria-busy={editor.refining}
        >
          <ResultIcon name="spark" /> Refine Research Objective
          {editor.refining && <LoadingDots />}
        </button>
      </div>
      {editor.notice && (
        <output className="editor-notice">{editor.notice}</output>
      )}
      {editor.error && (
        <div className="setup-error" role="alert">
          <ResultIcon name="caution" />
          <div>
            <strong>Your brief is safe</strong>
            <p>{editor.error}</p>
            <span>Your current writing stays in the editor.</span>
          </div>
        </div>
      )}
      <ResearchConfigurationPanel
        value={editor.configuration}
        onChange={editor.changeConfiguration}
        disabled={busy}
      />
      {editor.proposal && (
        <ResearchPlanReview
          original={editor.proposalOriginal}
          plan={editor.proposal}
          onChange={editor.setProposal}
          onAccept={editor.acceptProposal}
          onReject={editor.rejectProposal}
          stale={editor.proposalStale}
        />
      )}
      {editor.acceptedPlan && (
        <AcceptedResearchPlan plan={editor.acceptedPlan} />
      )}
      <dialog
        ref={dialog}
        className="expanded-objective-dialog"
        onCancel={close}
        onClose={() => setExpanded(false)}
        aria-labelledby="expanded-editor-title"
      >
        <div className="expanded-editor-header">
          <div>
            <span className="eyebrow">RESEARCH WRITING SPACE</span>
            <h2 id="expanded-editor-title">
              Keep the full investigation in view.
            </h2>
          </div>
          <button className="secondary-button" type="button" onClick={close}>
            Close writing space
          </button>
        </div>
        <label htmlFor="expanded-objective">
          Complete original research objective
        </label>
        <textarea
          ref={expandedInput}
          id="expanded-objective"
          value={objective}
          onChange={(event) => editor.changeObjective(event.target.value)}
          disabled={busy}
          aria-describedby="expanded-counter"
          spellCheck={false}
        />
        <span id="expanded-counter">
          {editorCounter} · Original text is never silently shortened
        </span>
      </dialog>
    </div>
  );
}
