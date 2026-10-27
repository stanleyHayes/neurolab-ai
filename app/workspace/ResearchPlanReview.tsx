import { ResearchLinesInput } from "./ResearchLinesInput";
import type { ResearchPlan } from "./research-editor-types";

type Props = {
  original: string;
  plan: ResearchPlan;
  onChange: (plan: ResearchPlan) => void;
  onAccept: () => void;
  onReject: () => void;
  stale: boolean;
};
export function ResearchPlanReview({
  original,
  plan,
  onChange,
  onAccept,
  onReject,
  stale,
}: Readonly<Props>) {
  return (
    <section className="research-plan-review" aria-labelledby="proposal-title">
      <span className="eyebrow">
        META PROPOSAL · NOT ACCEPTED · NO SCIENTIFIC RESULTS
      </span>
      <h3 id="proposal-title">Review the research plan</h3>
      <div className="objective-comparison">
        <div>
          <h4>Original objective · unchanged</h4>
          <pre className="objective-verbatim">{original}</pre>
        </div>
        <div>
          <label htmlFor="refined-objective">
            Proposed refined objective · editable
          </label>
          <textarea
            id="refined-objective"
            rows={10}
            value={plan.refined_objective}
            onChange={(event) =>
              onChange({ ...plan, refined_objective: event.target.value })
            }
          />
        </div>
      </div>
      <ResearchLinesInput
        id="proposed-questions"
        label="Proposed questions · one per line"
        value={plan.research_questions}
        onChange={(questions) =>
          onChange({ ...plan, research_questions: questions })
        }
      />
      <ResearchLinesInput
        id="proposed-hypotheses"
        label="Proposed hypotheses · one per line"
        value={plan.hypotheses}
        onChange={(hypotheses) => onChange({ ...plan, hypotheses })}
      />
      {plan.ambiguities.length > 0 && (
        <>
          <h4>Ambiguities to keep visible</h4>
          <ul>
            {plan.ambiguities.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}
      <h4>Proposed bounded tasks</h4>
      <ol>
        {plan.tasks.map((task) => (
          <li key={task.task_id}>
            <strong>{task.title}</strong>
            <p>{task.description}</p>
            <code>{task.tool_name ?? "Unsupported operation"}</code>
          </li>
        ))}
      </ol>
      {plan.dataset_suggestions.length > 0 && (
        <>
          <h4>Dataset suggestions</h4>
          <ul>
            {plan.dataset_suggestions.map((item) => (
              <li key={item.dataset_id}>
                {item.dataset_id} · {item.rationale} ·{" "}
                {item.enabled_for_analysis
                  ? "Analysis ready"
                  : "Reference only"}
              </li>
            ))}
          </ul>
        </>
      )}
      {plan.unsupported_requirements.length > 0 && (
        <div className="notice">
          <h4>Unsupported requirements</h4>
          <ul>
            {plan.unsupported_requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      {stale && (
        <p className="warning">
          Your original objective changed. Generate a new proposal before
          accepting it.
        </p>
      )}
      <div className="button-row">
        <button
          className="primary-button"
          type="button"
          disabled={stale || !plan.refined_objective.trim()}
          onClick={onAccept}
        >
          Accept research plan
        </button>
        <button className="secondary-button" type="button" onClick={onReject}>
          Reject proposal
        </button>
      </div>
    </section>
  );
}
export function AcceptedResearchPlan({
  plan,
}: Readonly<{ plan: ResearchPlan }>) {
  return (
    <details className="accepted-research-plan">
      <summary>Accepted research plan · {plan.tasks.length} tasks</summary>
      <h4>Refined objective · original retained separately</h4>
      <pre className="objective-verbatim">{plan.refined_objective}</pre>
      <ol>
        {plan.tasks.map((task) => (
          <li key={task.task_id}>
            <strong>{task.title}</strong> · {task.status}
            <p>{task.description}</p>
          </li>
        ))}
      </ol>
      {plan.unsupported_requirements.length > 0 && (
        <div className="notice">{plan.unsupported_requirements.join(" ")}</div>
      )}
    </details>
  );
}
