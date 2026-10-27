"use client";
import Link from "next/link";
import { useState } from "react";
import { EmptyState } from "./EmptyState";
import { ResultIcon } from "./ResultIcon";
import { finiteMeasure, ResultInterval } from "./ResultInterval";
import {
  ExtendedEvidence,
  extendedArtifactsForSection,
} from "./ExtendedEvidence";
import { ResultsProvenance, ResultsSummary } from "./ResultsSummary";
import type {
  ResearchArtifact,
  ResearchReport,
  WorkspaceSection,
} from "./workspace-types";

type EvidenceResultsProps = {
  section: WorkspaceSection;
  artifacts: ResearchArtifact[];
  report: ResearchReport | null;
  events: unknown[];
  retrieving: boolean;
  showContrast: boolean;
  showRanking: boolean;
  contrast: ResearchArtifact | undefined;
  ranking: ResearchArtifact | undefined;
  resultValues: Record<string, unknown>;
  means: Record<string, unknown>;
  topGenotypes: Array<Record<string, unknown>>;
  contrastCI: unknown;
  formatNumber: (value: unknown) => string;
  downloadFile: (filename: string, value: unknown, mime: string) => void;
};
function resultsTitle(section: WorkspaceSection): string {
  if (section === "genotype-explorer")
    return "Genotype evidence, in perspective.";
  if (section === "trait-analytics") return "The measured yield response.";
  if (section === "environments") return "Evidence across trial conditions.";
  return "What the field records show.";
}

function EvidenceExports({
  report,
  artifacts,
  events,
  downloadFile,
}: Readonly<
  Pick<EvidenceResultsProps, "report" | "artifacts" | "events" | "downloadFile">
>) {
  if (!report) return null;
  const csvRows = [
    "artifact_id,tool_name,claim_scope,sample_size,source_sha256",
    ...artifacts.map(
      (item) =>
        `${item.artifact_id},${item.tool_name},${item.claim_scope},${item.sample_size},${item.source_sha256}`,
    ),
  ];
  return (
    <footer className="results-export">
      <div>
        <span className="result-icon-tile">
          <ResultIcon name="record" />
        </span>
        <div>
          <h3>Take the evidence with you.</h3>
          <p>Source, seed, methods and recorded results stay together.</p>
        </div>
      </div>
      <div className="export-row">
        <button
          className="secondary-button"
          type="button"
          onClick={() =>
            downloadFile(
              `neurolab-${report.run_id}.json`,
              { report, artifacts, events },
              "application/json",
            )
          }
        >
          <ResultIcon name="download" />
          <span>Export evidence JSON</span>
        </button>
        <button
          className="text-button"
          type="button"
          onClick={() =>
            downloadFile(
              `neurolab-${report.run_id}.csv`,
              csvRows.join("\n"),
              "text/csv",
            )
          }
        >
          <ResultIcon name="record" />
          <span>Export artifact index CSV</span>
        </button>
      </div>
    </footer>
  );
}
function RegimeBars({
  means,
  formatNumber,
}: Readonly<{
  means: Record<string, unknown>;
  formatNumber: (value: unknown) => string;
}>) {
  const drought = finiteMeasure(means.DROUGHT);
  const watered = finiteMeasure(means.WELL_WATERED);
  const maximum = Math.max(drought ?? 0, watered ?? 0, 1);
  const rows = [
    { label: "Managed drought", value: drought, className: "drought" },
    { label: "Well-watered", value: watered, className: "watered" },
  ];
  return (
    <div
      className="results-regime-bars"
      aria-label="Mean grain yield by observed water regime"
    >
      {rows.map((row) => (
        <div className={`results-regime-row ${row.className}`} key={row.label}>
          <div>
            <span>
              <i aria-hidden="true" />
              {row.label}
            </span>
            <strong>
              {formatNumber(row.value)} <small>kg/ha</small>
            </strong>
          </div>
          <div className="results-regime-track" aria-hidden="true">
            {row.value !== null && row.value >= 0 && (
              <span style={{ width: `${(row.value / maximum) * 100}%` }} />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
function ContrastResult({
  artifact,
  results,
  means,
  interval,
  formatNumber,
}: Readonly<{
  artifact: ResearchArtifact;
  results: Record<string, unknown>;
  means: Record<string, unknown>;
  interval: unknown;
  formatNumber: (value: unknown) => string;
}>) {
  const validInterval =
    Array.isArray(interval) &&
    finiteMeasure(interval[0]) !== null &&
    finiteMeasure(interval[1]) !== null;
  return (
    <section
      className="results-panel results-contrast"
      aria-labelledby="contrast-heading"
    >
      <header className="results-panel-header">
        <span className="result-icon-tile">
          <ResultIcon name="comparison" />
        </span>
        <div>
          <span className="results-overline">Observed trial contrast</span>
          <h3 id="contrast-heading">Drought vs well-watered</h3>
        </div>
        <span className="result-sample">
          n = {formatNumber(artifact.sample_size)}
        </span>
      </header>
      <div className="results-primary-estimate">
        <p>Difference in observed mean yield</p>
        <div>
          {formatNumber(results.yield_difference_kg_ha)}
          <span>kg/ha</span>
        </div>
        <span className="estimate-direction">
          Managed drought minus well-watered · equal-weighted ENVT means
        </span>
      </div>
      <ResultInterval
        estimate={results.yield_difference_kg_ha}
        interval={interval}
        formatNumber={formatNumber}
      />
      <div className="results-interval-caption">
        <ResultIcon name="interval" />
        <div>
          <strong>95% block-bootstrap interval</strong>
          <p>
            {validInterval
              ? `${formatNumber(interval[0])} to ${formatNumber(interval[1])} kg/ha`
              : "Not recorded for this artifact"}
          </p>
        </div>
      </div>
      <RegimeBars means={means} formatNumber={formatNumber} />
      <p className="results-chart-note">
        These are observed descriptive means. The contrast does not isolate a
        causal effect of irrigation.
      </p>
      <div className="results-evidence-reference">
        <ResultIcon name="source" />
        <span>Evidence</span>
        <code>{artifact.artifact_id}</code>
      </div>
    </section>
  );
}
function ResultMethods({
  artifact,
  formatNumber,
}: Readonly<{
  artifact: ResearchArtifact;
  formatNumber: (value: unknown) => string;
}>) {
  const uncertainty = artifact.uncertainty;
  const method =
    typeof uncertainty?.method === "string"
      ? uncertainty.method
      : "Descriptive summary; no uncertainty model was recorded.";
  return (
    <aside className="results-context" aria-label="Methods and interpretation">
      <section className="results-panel results-methods">
        <header className="results-panel-header">
          <span className="result-icon-tile">
            <ResultIcon name="method" />
          </span>
          <div>
            <span className="results-overline">Reproducible by design</span>
            <h3>Behind the estimate</h3>
          </div>
        </header>
        <dl>
          <div>
            <dt>Observed records</dt>
            <dd>{formatNumber(artifact.sample_size)}</dd>
          </div>
          {uncertainty && (
            <>
              <div>
                <dt>Bootstrap samples</dt>
                <dd>{formatNumber(uncertainty.replicates)}</dd>
              </div>
              <div>
                <dt>Random seed</dt>
                <dd>{formatNumber(uncertainty.seed)}</dd>
              </div>
            </>
          )}
          <div>
            <dt>Claim scope</dt>
            <dd>{artifact.claim_scope}</dd>
          </div>
        </dl>
        <details>
          <summary>Method &amp; analysis version</summary>
          <p>{method}</p>
          <code>{artifact.analysis_version}</code>
        </details>
      </section>
      <section className="results-reading-note">
        <span className="result-icon-tile caution">
          <ResultIcon name="caution" />
        </span>
        <h3>Keep the design in view.</h3>
        <p>
          Exploratory evidence is a starting point for a follow-up trial, not a
          field recommendation.
        </p>
        <ul>
          {artifact.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </section>
    </aside>
  );
}
function GenotypeResults({
  ranking,
  genotypes,
  formatNumber,
}: Readonly<{
  ranking: ResearchArtifact;
  genotypes: Array<Record<string, unknown>>;
  formatNumber: (value: unknown) => string;
}>) {
  const [expanded, setExpanded] = useState(false);
  const all = Array.isArray(ranking.results.genotypes)
    ? (ranking.results.genotypes as Array<Record<string, unknown>>)
    : genotypes;
  const entries = expanded ? all : genotypes.slice(0, 8);
  const maximum = Math.max(
    ...all.map(
      (item) => finiteMeasure(item.equal_environment_mean_yield_kg_ha) ?? 0,
    ),
    1,
  );
  if (!entries.length)
    return (
      <EmptyState
        compact
        icon="evidence"
        title="No genotype rows in this result"
        description="The saved artifact has no displayable genotype summaries. Its source and export remain available."
      />
    );
  return (
    <section
      className="results-panel results-genotypes"
      aria-labelledby="genotype-heading"
    >
      <header className="results-panel-header">
        <span className="result-icon-tile">
          <ResultIcon name="genotype" />
        </span>
        <div>
          <span className="results-overline">
            Candidates for further research
          </span>
          <h3 id="genotype-heading">Highest observed drought means</h3>
        </div>
        <span className="result-sample">
          {entries.length} of {all.length} genotypes
        </span>
      </header>
      <p className="results-panel-description">
        Equal-environment mean grain yield. A high observed mean does not
        establish drought tolerance or ranking stability.
      </p>
      <section
        className="results-table-scroll"
        aria-label="Scrollable genotype result table"
      >
        <table className="results-genotype-table">
          <caption className="sr-only">
            Descriptive drought genotype yields in kg/ha, plot counts and
            observed ENVT coverage
          </caption>
          <thead>
            <tr>
              <th scope="col">Rank</th>
              <th scope="col">Genotype</th>
              <th scope="col">
                Mean yield <span>kg/ha</span>
              </th>
              <th scope="col">Plots</th>
              <th scope="col">ENVT indices</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, index) => {
              const value = finiteMeasure(
                entry.equal_environment_mean_yield_kg_ha,
              );
              const genotype =
                typeof entry.genotype_id === "string"
                  ? entry.genotype_id
                  : "Identifier not recorded";
              return (
                <tr
                  key={genotype}
                  className={index === 0 ? "leading-genotype" : ""}
                >
                  <td>
                    <span className="results-rank">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                  </td>
                  <th scope="row">{genotype}</th>
                  <td>
                    <span className="genotype-yield-value">
                      {formatNumber(value)}
                    </span>
                    <span className="genotype-yield-track" aria-hidden="true">
                      {value !== null && value >= 0 && (
                        <span
                          style={{ width: `${(value / maximum) * 100}%` }}
                        />
                      )}
                    </span>
                  </td>
                  <td>{formatNumber(entry.plot_count)}</td>
                  <td>{formatNumber(entry.environment_count)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      <div className="results-table-footer">
        <span>
          <ResultIcon name="interval" />
          Ranking uncertainty was not estimated.
        </span>
        {all.length > 8 && (
          <button
            className="text-button"
            type="button"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded
              ? "Show leading genotypes"
              : `Show all ${all.length} genotypes`}
          </button>
        )}
      </div>
      <details className="results-ranking-caveats">
        <summary>Ranking method &amp; limitations</summary>
        <ul>
          {ranking.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
        <code>{ranking.artifact_id}</code>
      </details>
    </section>
  );
}
function AnalysisScopeNote({
  section,
  available,
}: Readonly<{ section: WorkspaceSection; available: boolean }>) {
  if (available) return null;
  if (section !== "trait-analytics" && section !== "environments") return null;
  const message =
    section === "trait-analytics"
      ? "No trait-correlation artifact is included in this view. The measured yield comparison below does not establish which plant traits are associated with resilience."
      : "The contrast is stratified by observed trial design. It does not estimate a genotype stability statistic or turn ENVT indices into calendar years.";
  return (
    <div className="results-scope-note">
      <ResultIcon name="record" />
      <p>{message}</p>
    </div>
  );
}
export function EvidenceResults(props: Readonly<EvidenceResultsProps>) {
  const {
    section,
    artifacts,
    report,
    events,
    retrieving,
    showContrast,
    showRanking,
    contrast,
    ranking,
    resultValues,
    means,
    topGenotypes,
    contrastCI,
    formatNumber,
    downloadFile,
  } = props;
  const extended = extendedArtifactsForSection(artifacts, section);
  const hasResult = Boolean(
    (showContrast && contrast) || (showRanking && ranking) || extended.length,
  );
  const sourceConsistent =
    !report ||
    artifacts.every(
      (artifact) => artifact.source_sha256 === report.source_sha256,
    );
  const mode =
    report?.mode === "meta"
      ? `${report.model_provider ?? "Configured provider"} · ${report.model_id ?? "model not recorded"}`
      : "Deterministic replay · no model call";
  return (
    <article className="card evidence-card results-workbench" id="evidence">
      <header className="results-heading">
        <div>
          <span className="results-overline">
            <ResultIcon name="evidence" />
            Evidence workspace
          </span>
          <h2>{resultsTitle(section)}</h2>
          <p>
            Real field records. Transparent methods. A measured starting point.
          </p>
        </div>
        <div className="results-run-badges">
          <span className="results-status">
            <ResultIcon name="complete" />
            {artifacts.length} saved artifacts
          </span>
          {report && <span className="results-mode">{mode}</span>}
          {report && (
            <Link className="primary-link" href="/live-experiment">
              <ResultIcon name="retention" /> Cinematic replay
            </Link>
          )}
        </div>
      </header>
      {report && report.completion_status !== "complete" && (
        <output className="results-partial">
          <ResultIcon name="caution" />
          <span>
            Partial report: requested analyses remain incomplete. Review the
            recorded evidence and limitations before interpreting these results.
          </span>
        </output>
      )}
      {!sourceConsistent && (
        <p className="auth-error" role="alert">
          Saved artifact source hashes do not match this report. Comparisons are
          withheld until the source inconsistency is resolved.
        </p>
      )}
      <AnalysisScopeNote section={section} available={extended.length > 0} />
      {retrieving && (
        <output
          className="results-loading"
          aria-label="Retrieving persisted experiment results"
        >
          <span className="sr-only">
            Retrieving persisted experiment results
          </span>
          <span className="skeleton results-summary-skeleton" />
          <span className="skeleton results-chart-skeleton" />
        </output>
      )}
      {!retrieving && sourceConsistent && hasResult && (
        <>
          {(contrast || ranking) && (
            <ResultsSummary
              contrast={contrast}
              ranking={ranking}
              formatNumber={formatNumber}
            />
          )}
          <div className="results-analysis-grid">
            {showContrast && contrast && (
              <ContrastResult
                artifact={contrast}
                results={resultValues}
                means={means}
                interval={contrastCI}
                formatNumber={formatNumber}
              />
            )}
            {showContrast && contrast && (
              <ResultMethods artifact={contrast} formatNumber={formatNumber} />
            )}
          </div>
          {showRanking && ranking && (
            <GenotypeResults
              key={ranking.artifact_id}
              ranking={ranking}
              genotypes={topGenotypes}
              formatNumber={formatNumber}
            />
          )}
          <ExtendedEvidence artifacts={extended} />
          {showContrast && !contrast && (
            <EmptyState
              compact
              icon="evidence"
              title="No regime comparison in this run"
              description="A regime contrast requires a separate completed tool artifact."
            />
          )}
          {showRanking && !ranking && (
            <EmptyState
              compact
              icon="evidence"
              title="No genotype summaries in this run"
              description="No ranking result was computed in this run."
            />
          )}
        </>
      )}
      {!retrieving && !hasResult && (
        <EmptyState
          icon="evidence"
          title="A clearer view starts with recorded evidence."
          description="This run has no comparison or genotype result for this page. Start an investigation to compute real results from the Ghana trial records."
          action={
            <Link className="primary-link" href="/experiment-studio">
              Start an investigation <span aria-hidden="true">↗</span>
            </Link>
          }
        />
      )}
      <ResultsProvenance report={report} artifacts={artifacts} />
      <EvidenceExports
        report={report}
        artifacts={artifacts}
        events={events}
        downloadFile={downloadFile}
      />
    </article>
  );
}
