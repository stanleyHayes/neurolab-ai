import Link from "next/link";
import { EvidenceBundleButton } from "./EvidenceBundleButton";
import { InlineMeasure } from "./EvidenceVisualizations";
import { finiteMeasure } from "./ResultInterval";
import { ResultIcon } from "./ResultIcon";
import type {
  ResearchReport,
  ScientificHypothesis,
  ScientificReport,
} from "./workspace-types";
const number = (value: unknown, digits = 1) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : "—";
const verdictLabel = (value: string) =>
  ({
    criterion_met: "Observed criterion met",
    criterion_not_met: "Observed criterion not met",
    inconclusive: "Inconclusive",
    not_assessed: "Not assessed",
  })[value] ?? value;
function EvidenceIds({ ids }: Readonly<{ ids: string[] }>) {
  return (
    <p className="scientific-evidence-ids">
      Evidence: {ids.length ? ids.join(", ") : "not available"}
    </p>
  );
}
function HypothesisCard({ item }: Readonly<{ item: ScientificHypothesis }>) {
  return (
    <article className="scientific-hypothesis">
      <div className="scientific-hypothesis-state">
        <span>{item.id}</span>
        <strong>{verdictLabel(item.verdict)}</strong>
      </div>
      <h3>{item.proposal}</h3>
      <p>
        <b>Rationale.</b> {item.rationale}
      </p>
      <details>
        <summary>Declared evaluation criterion</summary>
        <p>{item.criterion}</p>
      </details>
      <p className="scientific-finding">{item.findings}</p>
      {item.matching_genotype_ids && item.matching_genotype_ids.length > 0 && (
        <p>
          <b>Observed qualifying IDs:</b>{" "}
          {item.matching_genotype_ids.join(", ")}
        </p>
      )}
      {item.contradictions.length > 0 && (
        <div className="scientific-contradictions">
          <b>Counter-evidence and uncertainty</b>
          <ul>
            {item.contradictions.map((value) => (
              <li key={value}>{value}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="caption">{item.scope}</p>
      <EvidenceIds ids={item.evidence_ids} />
    </article>
  );
}
function consistencyLabel(value: boolean | null | undefined) {
  if (value === null || value === undefined) return "Not assessed";
  return value ? "Met" : "Not met";
}
function CandidateTable({ science }: Readonly<{ science: ScientificReport }>) {
  const entries = science.candidate_summaries ?? [];
  const yieldMaximum = Math.max(
    1,
    ...entries.flatMap((item) => [
      finiteMeasure(item.drought_mean_kg_ha) ?? 0,
      finiteMeasure(item.observed_regime_summary?.well_watered_mean_kg_ha) ?? 0,
    ]),
  );
  return (
    <section
      className="scientific-section"
      aria-label="Exploratory candidate trade-offs"
    >
      <span className="results-overline">
        <ResultIcon name="genotype" /> CANDIDATE TRADE-OFFS
      </span>
      <h3>Large observed means do not tell the whole story.</h3>
      {science.observational_answer && (
        <p>{science.observational_answer.summary}</p>
      )}
      <p>
        These are the five largest complete-coverage drought means. Retention
        compares separately summarized regimes; it is not a causal tolerance
        score. Rank ranges come from omitting each observed environment, not a
        confidence interval.
      </p>
      <section
        className="results-table-scroll"
        aria-label="Candidate summary table"
      >
        <table className="extended-evidence-table">
          <caption>
            Observed grain yield in kg/ha · descriptive candidate summaries
          </caption>
          <thead>
            <tr>
              <th scope="col">Genotype</th>
              <th scope="col">Drought mean</th>
              <th scope="col">Watered mean</th>
              <th scope="col">Retention %</th>
              <th scope="col">Environment-mean SD</th>
              <th scope="col">Omitted-environment ranks</th>
              <th scope="col">Plots D / W</th>
              <th scope="col">Top quartile in every observed environment</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((item) => (
              <tr key={item.genotype_id}>
                <th scope="row">{item.genotype_id}</th>
                <td>
                  <InlineMeasure
                    value={item.drought_mean_kg_ha}
                    maximum={yieldMaximum}
                    formatted={number(item.drought_mean_kg_ha)}
                  />
                </td>
                <td>
                  <InlineMeasure
                    value={
                      item.observed_regime_summary?.well_watered_mean_kg_ha
                    }
                    maximum={yieldMaximum}
                    formatted={number(
                      item.observed_regime_summary?.well_watered_mean_kg_ha,
                    )}
                  />
                </td>
                <td>
                  {number(
                    item.observed_regime_summary?.descriptive_retention_percent,
                  )}
                </td>
                <td>{number(item.environment_mean_sd_kg_ha)}</td>
                <td>
                  {item.omitted_environment_rank_range
                    ?.map((value) => number(value))
                    .join("–") ?? "Not estimated"}
                </td>
                <td>
                  {number(item.observed_regime_summary?.drought_plot_count, 0)}{" "}
                  /{" "}
                  {number(
                    item.observed_regime_summary?.well_watered_plot_count,
                    0,
                  )}
                </td>
                <td>
                  {consistencyLabel(
                    item.meets_observed_top_quartile_each_environment,
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {entries.length > 0 && (
        <p className="caption">
          Yield bars share a zero-based scale from 0 to {number(yieldMaximum)}{" "}
          kg/ha within this table. Numeric estimates remain printed above each
          bar.
        </p>
      )}
      {!entries.length && <p>No complete candidate evidence is available.</p>}
      <p className="caption">
        A ratio above 100% can reflect differing trial environments or a low
        watered denominator; it does not show that drought causally increased
        yield. No combined tolerance/stability score or ranking confidence was
        estimated.
      </p>
      <EvidenceIds
        ids={[...new Set(entries.flatMap((entry) => entry.evidence_ids))]}
      />
    </section>
  );
}
function TraitScreen({ science }: Readonly<{ science: ScientificReport }>) {
  const traits = science.findings?.trait_associations;
  if (!traits) return null;
  return (
    <section
      className="scientific-section"
      aria-label="Seven-trait exploratory screen"
    >
      <span className="results-overline">
        <ResultIcon name="genotype" /> ALL MEASURED TRAIT ASSOCIATIONS
      </span>
      <h3>Which characteristics accompany observed drought yield?</h3>
      <p>{traits.screen_summary}</p>
      <section
        className="results-table-scroll"
        aria-label="Scientific trait association table"
      >
        <table className="extended-evidence-table">
          <caption>
            Seven-trait screen · one genotype mean per point · no multiplicity
            correction
          </caption>
          <thead>
            <tr>
              <th scope="col">Measured trait</th>
              <th scope="col">Unit</th>
              <th scope="col">Genotypes</th>
              <th scope="col">Spearman rho</th>
              <th scope="col">Conditional 95% resampling interval</th>
            </tr>
          </thead>
          <tbody>
            {traits.associations.map((trait) => (
              <tr key={trait.trait}>
                <th scope="row">{trait.trait.replaceAll("_", " ")}</th>
                <td>{trait.unit}</td>
                <td>{number(trait.genotype_count, 0)}</td>
                <td>{number(trait.spearman_rho, 3)}</td>
                <td>
                  {trait.spearman_rho_95_percentile_interval
                    ?.map((value) => number(value, 3))
                    .join(" to ") ?? "Not estimated"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="caption">
        These associations describe observed drought yield, not independently
        measured causal resilience. Stay-green score direction is unverified;
        conditional genotype-profile intervals ignore relatedness, selection and
        future-environment sampling.
      </p>
      <EvidenceIds ids={traits.evidence_ids} />
    </section>
  );
}

function MethodAndSources({
  science,
}: Readonly<{ science: ScientificReport }>) {
  return (
    <details className="scientific-methods">
      <summary>Dataset sources, methodology and reproducibility</summary>
      {science.source_citations?.map((source) => (
        <p key={source.doi}>
          <a
            href={`https://doi.org/${source.doi}`}
            target="_blank"
            rel="noreferrer"
          >
            {source.authors} · DOI {source.doi} ↗
          </a>
          <br />
          {source.license}. {source.role}.
        </p>
      ))}
      <p>
        <b>Dependent variable:</b> {science.methodology?.dependent_variable}
      </p>
      <p>
        <b>Explanatory variables:</b>{" "}
        {science.methodology?.explanatory_variables}
      </p>
      <p>{science.methodology?.design}</p>
      <ol>
        {science.methodology?.methods.map((method) => (
          <li key={method.evidence_id}>
            <b>{method.tool}</b> · {method.analysis_version} · source records=
            {method.sample_size}
            {method.uncertainty ? (
              <pre>{JSON.stringify(method.uncertainty, null, 2)}</pre>
            ) : (
              <p>No interval recorded for this tool.</p>
            )}
            <EvidenceIds ids={[method.evidence_id]} />
          </li>
        ))}
      </ol>
      <h3>Audited source inventory</h3>
      <p>
        Physical and substantive records are file-level audit counts. They must
        not be summed as independent plots. Component files overlap the Ghana
        combined source; IITA remains reference-only.
      </p>
      <section
        className="results-table-scroll"
        aria-label="Audited source files"
      >
        <table className="extended-evidence-table">
          <caption>
            Source bytes verified at profile-tool execution; original staging
            columns retained
          </caption>
          <thead>
            <tr>
              <th scope="col">Source file</th>
              <th scope="col">Physical records</th>
              <th scope="col">Substantive records</th>
              <th scope="col">Use and limitations</th>
            </tr>
          </thead>
          <tbody>
            {science.dataset_inventory?.map((source) => (
              <tr key={source.source_file}>
                <th scope="row">
                  {source.source_file}
                  <small>{source.source_sha256}</small>
                </th>
                <td>{number(source.physical_rows, 0)}</td>
                <td>{number(source.substantive_rows, 0)}</td>
                <td>
                  <b>
                    {source.analysis_enabled
                      ? "Canonical analysis"
                      : "Not pooled"}
                  </b>
                  <p>{source.eligibility_reason}</p>
                  <details>
                    <summary>Original columns and audit provenance</summary>
                    <p>{source.original_columns.join(", ")}</p>
                    <p>{source.count_provenance}</p>
                    <p>
                      Fully empty records: {number(source.fully_empty_rows, 0)}
                    </p>
                  </details>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <EvidenceIds ids={science.dataset_inventory_evidence_ids ?? []} />
      <h3>Loaded code identity</h3>
      <p>
        {science.reproducibility?.snapshot}. Python{" "}
        {science.reproducibility?.python_version}.
      </p>
      <p>
        Commit:{" "}
        <code>{science.reproducibility?.code_commit ?? "not available"}</code>
      </p>
      <p>{science.reproducibility?.dirty_status_note}</p>
      <dl>
        {Object.entries(science.reproducibility?.module_sha256 ?? {}).map(
          ([path, hash]) => (
            <div key={path}>
              <dt>{path}</dt>
              <dd>
                <code>{hash}</code>
              </dd>
            </div>
          ),
        )}
      </dl>
      <h3>Scientific method limitations</h3>
      <ul>
        {science.methodology?.assumptions_and_limits.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </details>
  );
}
export function ScientificReportView({
  report,
  downloadFile,
}: Readonly<{
  report: ResearchReport;
  downloadFile: (name: string, value: unknown, mime: string) => void;
}>) {
  const science = report.scientific_report;
  if (!science) return null;
  const comparison = science.findings?.observed_regime_comparison;
  const next = science.next_experiment;
  const follow = science.follow_up_analysis;
  return (
    <article
      className="card scientific-report"
      aria-label="Exploratory Ghana scientific report"
    >
      <header className="scientific-report-header">
        <div>
          <span className="results-overline">
            <ResultIcon name="record" /> EXPLORATORY SCIENTIFIC REPORT
          </span>
          <h2>What the observed trials can tell us.</h2>
          <p>{science.scope}</p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() =>
            downloadFile(
              `neurolab-${report.run_id}-scientific-report.json`,
              { report },
              "application/json",
            )
          }
        >
          <ResultIcon name="download" /> Export scientific report
        </button>
      </header>
      <div className="export-row">
        <EvidenceBundleButton
          runId={report.run_id}
          downloadFile={downloadFile}
        />
        <p className="caption">
          The evidence bundle includes the saved report, numeric artifacts and
          recorded events for reproducible figure export.
        </p>
      </div>
      <div className="scientific-scope">
        <ResultIcon name="caution" />
        <p>
          <b>
            Run: {report.completion_status}. Evidence coverage:{" "}
            {science.evidence_coverage}.
          </b>{" "}
          Completing the workflow does not establish causal drought tolerance,
          broad adaptation or a field recommendation. Hypotheses use
          retrospective operational criteria, with conditional uncertainty and
          no confirmatory significance tests.
        </p>
      </div>
      {science.evidence_coverage === "source_mismatch" && (
        <p role="alert">
          Source hashes disagree. Combined interpretation is withheld.
        </p>
      )}
      {science.missing_tools && science.missing_tools.length > 0 && (
        <p className="scientific-contradictions">
          Unexecuted evidence: {science.missing_tools.join(", ")}. Missing
          results are not inferred.
        </p>
      )}
      {science.additional_hypotheses_not_assessed &&
        science.additional_hypotheses_not_assessed.length > 0 && (
          <section className="scientific-contradictions">
            <h3>Additional proposals remain unassessed</h3>
            <p>
              The fixed profile does not substitute its criteria for these
              user-supplied hypotheses. They remain preserved; the run is
              partial.
            </p>
            <ul>
              {science.additional_hypotheses_not_assessed.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </section>
        )}
      {comparison && (
        <section className="scientific-section">
          <h3>Observed regime comparison</h3>
          <dl className="scientific-summary">
            <div>
              <dt>Drought mean</dt>
              <dd>
                {number(comparison.results.mean_yield_by_regime.DROUGHT)}{" "}
                <small>kg/ha</small>
              </dd>
            </div>
            <div>
              <dt>Well-watered mean</dt>
              <dd>
                {number(comparison.results.mean_yield_by_regime.WELL_WATERED)}{" "}
                <small>kg/ha</small>
              </dd>
            </div>
            <div>
              <dt>Descriptive retention</dt>
              <dd>
                {number(
                  comparison.results
                    .drought_to_well_watered_yield_ratio_percent,
                )}{" "}
                <small>%</small>
              </dd>
            </div>
          </dl>
          <p>
            Observed drought-minus-watered difference:{" "}
            {number(comparison.results.yield_difference_kg_ha)} kg/ha. 95%
            block-bootstrap interval:{" "}
            {comparison.uncertainty.yield_difference_95_ci_kg_ha
              .map((value) => number(value))
              .join(" to ")}{" "}
            kg/ha. Water regime and environment are confounded; this is not a
            causal irrigation estimate.
          </p>
          <EvidenceIds ids={comparison.evidence_ids} />
        </section>
      )}
      <section
        className="scientific-section"
        aria-label="Hypothesis evaluations"
      >
        <span className="results-overline">
          <ResultIcon name="method" /> DECLARED HYPOTHESES &amp; RECORDED
          EVIDENCE
        </span>
        <h3>Evaluate the question, including uncertainty.</h3>
        <div className="scientific-hypotheses">
          {science.hypothesis_evaluations.map((item) => (
            <HypothesisCard key={item.id} item={item} />
          ))}
        </div>
      </section>
      <TraitScreen science={science} />
      <CandidateTable science={science} />
      {follow && (
        <section className="scientific-section scientific-followup">
          <span className="results-overline">
            <ResultIcon name="retention" /> FOLLOW-UP ANALYSIS
          </span>
          <h3>{follow.analysis}</h3>
          <p>
            <b>
              {follow.executed ? "Calculation executed" : "Not executed"} ·{" "}
              {follow.adaptively_selected
                ? "Selected using observed evidence"
                : "No adaptive selection claimed"}
              .
            </b>{" "}
            {follow.selection_source}
          </p>
          <p>{follow.uncertainty_addressed}</p>
          <p>{follow.remaining_uncertainty}</p>
          <EvidenceIds
            ids={[
              ...follow.selection_evidence_ids,
              ...follow.result_evidence_ids,
            ]}
          />
        </section>
      )}
      {next && (
        <section className="scientific-section scientific-next">
          <span className="results-overline">
            <ResultIcon name="plots" /> PROPOSAL ONLY · NOT EXECUTED
          </span>
          <h3>{next.title}</h3>
          <p>{next.design}</p>
          <p>
            Candidate IDs for investigation, subject to seed/identity
            verification: {next.candidate_ids.join(", ") || "not established"}.
          </p>
          <h4>Additional data that would improve confidence</h4>
          <ul>
            {next.additional_data.map((value) => (
              <li key={value}>{value}</li>
            ))}
          </ul>
          <p>{next.analysis_plan}</p>
          <p>
            <b>Sample size:</b> {next.sample_size}
          </p>
          <a href={next.reference.url} target="_blank" rel="noreferrer">
            Design reference: {next.reference.title} ↗
          </a>
          <EvidenceIds ids={next.basis_evidence_ids} />
        </section>
      )}
      <div className="scientific-visual-links">
        <Link className="secondary-link" href="/research-results">
          Measured results and visualizations ↗
        </Link>
        <Link className="secondary-link" href="/live-experiment">
          Replay the recorded processing ↗
        </Link>
      </div>
      <MethodAndSources science={science} />
      <div className="scientific-unresolved">
        <h3>What this study cannot establish</h3>
        <ul>
          {science.unresolved_scope?.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}
