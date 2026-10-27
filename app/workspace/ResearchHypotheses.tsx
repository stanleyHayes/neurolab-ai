import { ResultIcon } from "./ResultIcon";

export function ResearchHypotheses({
  hypotheses,
  constraints,
}: Readonly<{ hypotheses: string[]; constraints: string[] }>) {
  const proposals = hypotheses.map((text, index) => {
    const prefix = `${text} Rationale: `;
    const original = constraints.find(
      (item) =>
        item.startsWith(prefix) && item.includes(" Criterion: ", prefix.length),
    );
    const detail = original?.slice(prefix.length);
    const boundary = detail?.indexOf(" Criterion: ") ?? -1;
    const identifier = /^(H\d+):\s*/.exec(text);
    return {
      text,
      label: identifier?.[1] ?? `Proposal ${index + 1}`,
      proposal: identifier ? text.slice(identifier[0].length) : text,
      original,
      rationale: detail?.slice(0, boundary),
      criterion: detail?.slice(boundary + " Criterion: ".length),
    };
  });
  const paired = new Set(
    proposals.map((item) => item.original).filter(Boolean),
  );
  const notes = constraints.filter((item) => !paired.has(item));
  return (
    <>
      {proposals.length > 0 && (
        <section className="plan-hypotheses" aria-label="Proposed hypotheses">
          <div className="plan-section-heading">
            <span className="plan-section-icon">
              <ResultIcon name="method" />
            </span>
            <div>
              <h3>Proposed hypotheses</h3>
              <p>Persisted proposals · not scientific results</p>
            </div>
            <span className="plan-section-count">
              {proposals.length} proposals
            </span>
          </div>
          <ol className="hypothesis-card-grid" role="list">
            {proposals.map((item, index) => (
              <li className="hypothesis-card" key={`${index}:${item.text}`}>
                <div className="hypothesis-card-label">
                  <span>{item.label}</span>
                  <span>Proposed</span>
                </div>
                <h4>{item.proposal}</h4>
                {item.rationale && (
                  <div className="hypothesis-rationale">
                    <h5>
                      <ResultIcon name="source" /> Rationale
                    </h5>
                    <p>{item.rationale}</p>
                  </div>
                )}
                {item.criterion && (
                  <div className="hypothesis-criterion">
                    <h5>
                      <ResultIcon name="interval" /> Evaluation criterion
                    </h5>
                    <p>{item.criterion}</p>
                  </div>
                )}
                {item.original && (
                  <details className="hypothesis-original">
                    <summary>Original saved constraint</summary>
                    <p>{item.original}</p>
                  </details>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}
      {constraints.length > 0 && (
        <section
          className="plan-boundaries"
          aria-label="Preserved research constraints"
        >
          <div className="plan-section-heading">
            <span className="plan-section-icon">
              <ResultIcon name="caution" />
            </span>
            <div>
              <h3>Preserved research constraints</h3>
              <p>
                {paired.size > 0
                  ? `${paired.size} saved criteria are shown with their hypotheses above.`
                  : "Scope and interpretation limits retained from the saved plan."}
              </p>
            </div>
          </div>
          {notes.length > 0 && (
            <ul className="plan-boundary-notes" role="list">
              {notes.map((note, index) => (
                <li key={`${index}:${note}`}>
                  <ResultIcon name="record" />
                  <p>{note}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}
