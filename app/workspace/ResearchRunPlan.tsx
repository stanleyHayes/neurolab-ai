import Link from "next/link";
import { ResultIcon } from "./ResultIcon";
import { ResearchHypotheses } from "./ResearchHypotheses";
import type { ResearchReport } from "./workspace-types";

export function ResearchRunPlan({
  report,
}: Readonly<{ report: ResearchReport }>) {
  return (
    <article
      className="card research-run-plan"
      aria-labelledby="run-plan-title"
    >
      <span className="eyebrow">PERSISTED INVESTIGATION CONTRACT</span>
      <div className="run-plan-heading">
        <h2 id="run-plan-title">Original objective &amp; execution plan</h2>
        <Link
          href="/live-experiment"
          className="secondary-button plan-cinematic-link"
        >
          <ResultIcon name="retention" /> Watch cinematic replay{" "}
          <ResultIcon name="arrow" />
        </Link>
      </div>
      <h3>Original objective · exact submitted text</h3>
      <pre className="objective-verbatim">{report.objective}</pre>
      {report.refined_objective && (
        <>
          <h3>Refined objective · original retained</h3>
          <pre className="objective-verbatim">{report.refined_objective}</pre>
        </>
      )}
      {report.research_plan ? (
        <>
          <p className="caption">
            Planning mode: {report.research_plan.planning_mode}. Hypotheses are
            proposals, not scientific results.
          </p>
          <ResearchHypotheses
            hypotheses={report.research_plan.hypotheses}
            constraints={report.research_plan.important_constraints ?? []}
          />
          {report.research_plan.ambiguities?.length > 0 && (
            <div className="notice">
              <h3>Planning limits and unresolved questions</h3>
              <ul>
                {report.research_plan.ambiguities.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          <h3>Task completion and recorded evidence</h3>
          <ol className="run-plan-task-list">
            {report.research_plan.tasks.map((task) => (
              <li key={task.task_id}>
                <div>
                  <strong>{task.title}</strong>
                  <span className="task-state">{task.status}</span>
                </div>
                <p>{task.description}</p>
                <code>{task.tool_name ?? "Unsupported operation"}</code>
                {task.evidence_ids.length > 0 && (
                  <p className="caption">
                    Evidence: {task.evidence_ids.join(", ")}
                  </p>
                )}
              </li>
            ))}
          </ol>
          {report.research_plan.unsupported_requirements.length > 0 && (
            <div className="notice">
              <h3>Unmet research requirements</h3>
              <ul>
                {report.research_plan.unsupported_requirements.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      ) : (
        <p className="caption">
          This historical run has no persisted structured plan. Its original
          objective and recorded artifacts remain available.
        </p>
      )}
    </article>
  );
}
