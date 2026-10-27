import Link from "next/link";
import { EmptyState } from "./EmptyState";
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
    return "Observed drought genotype summaries";
  if (section === "trait-analytics") return "Observed grain-yield analysis";
  if (section === "environments") return "Observed environment comparison";
  return "Research results";
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
        Export evidence JSON
      </button>
      <button
        className="secondary-button"
        type="button"
        onClick={() =>
          downloadFile(
            `neurolab-${report.run_id}.csv`,
            csvRows.join("\n"),
            "text/csv",
          )
        }
      >
        Export artifact index CSV
      </button>
    </div>
  );
}

type ContrastResultProps = {
  artifact: ResearchArtifact;
  results: Record<string, unknown>;
  means: Record<string, unknown>;
  interval: unknown;
  formatNumber: (value: unknown) => string;
};

function ContrastResult({
  artifact,
  results,
  means,
  interval,
  formatNumber,
}: Readonly<ContrastResultProps>) {
  if (!artifact) return null;
  const max = Math.max(
    Number(means.DROUGHT) || 0,
    Number(means.WELL_WATERED) || 0,
    1,
  );
  const rows: Array<[string, unknown]> = [
    ["Managed drought", means.DROUGHT],
    ["Well-watered", means.WELL_WATERED],
  ];

  return (
    <div className="contrast-panel">
      <div className="result-title">
        DROUGHT − WELL-WATERED · EQUAL-WEIGHTED ENVT MEANS
      </div>
      <div className="contrast-number">
        {formatNumber(results.yield_difference_kg_ha)} <span>kg/ha</span>
      </div>
      <div className="interval">
        95% block-bootstrap interval · [
        {Array.isArray(interval)
          ? `${formatNumber(interval[0])}, ${formatNumber(interval[1])}`
          : "not available"}
        ]
      </div>
      <div
        className="mean-bars"
        aria-label="Mean grain yield by observed water regime"
      >
        {rows.map(([label, value]) => {
          const amount = typeof value === "number" ? value : 0;
          return (
            <div className="mean-row" key={label}>
              <div className="mean-label">
                <span>{label}</span>
                <b>{formatNumber(value)} kg/ha</b>
              </div>
              <div className="mean-track" aria-hidden="true">
                <span
                  style={{ width: `${Math.max(2, (amount / max) * 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <p className="caption">
        Observed descriptive means, not a causal treatment effect.
        Equal-weighted environment summary.
      </p>
      <div className="notice result-notice">{artifact.warnings.join(" ")}</div>
    </div>
  );
}

function GenotypeResults({
  ranking,
  genotypes,
  showContrast,
  hasContrast,
}: Readonly<{
  ranking: ResearchArtifact | undefined;
  genotypes: Array<Record<string, unknown>>;
  showContrast: boolean;
  hasContrast: boolean;
}>) {
  if (!ranking) return null;
  if (!genotypes.length)
    return (
      <EmptyState
        compact
        icon="evidence"
        title="No genotype rows in this result"
        description="The saved analysis includes a ranking artifact without displayable genotype rows. Try a new analysis or reopen another saved run."
        action={
          <Link className="text-link" href="/experiment-studio">
            Start a new experiment ↗
          </Link>
        }
      />
    );
  const maximum = Math.max(
    ...genotypes.map(
      (item) => Number(item.equal_environment_mean_yield_kg_ha) || 0,
    ),
    1,
  );

  return (
    <div className="genotype-panel">
      <div className="panel-title-row">
        <h3>Drought genotype summaries</h3>
        <span>DESCRIPTIVE · NOT A RECOMMENDATION</span>
      </div>
      <p className="caption">
        Top observed equal-environment means · yield kg/ha
      </p>
      <ol
        className="rank-list"

        aria-label="Top drought genotype yield summaries"
      >
        {genotypes.map((entry, index) => {
          const value = Number(entry.equal_environment_mean_yield_kg_ha) || 0;
          return (
            <li
              className="rank-row"

              key={String(entry.genotype_id)}
            >
              <span className="rank-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              <strong>{String(entry.genotype_id)}</strong>
              <span className="rank-track" aria-hidden="true">
                <span style={{ width: `${(value / maximum) * 100}%` }} />
              </span>
              <b>
                {value.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </b>
            </li>
          );
        })}
      </ol>
      {ranking.warnings.map((warning) => (
        <p className="caption warning" key={warning}>
          {warning}
        </p>
      ))}
      {showContrast && !hasContrast && (
        <EmptyState
          compact
          icon="evidence"
          title="No regime comparison yet"
          description="This saved run includes genotype summaries but no regime comparison artifact."
          action={
            <Link className="text-link" href="/experiment-studio">
              Start a new experiment ↗
            </Link>
          }
        />
      )}
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
  const hasAnyRequestedArtifact =
    (!showContrast || Boolean(contrast)) && (!showRanking || Boolean(ranking));

  const renderedChoice1 = (() => {
    if (showContrast && showRanking) {
      return "Evidence appears after a persisted run";
    }
    if (showContrast) {
      return "No regime comparison yet";
    }
    return "No genotype summaries yet";
  })();
  const renderedChoice2 = (() => {
    if (showContrast && showRanking) {
      return "Start a run to calculate a regime comparison and genotype summaries from the observed Ghana trial dataset.";
    }
    if (showContrast) {
      return "Run an analysis to calculate an observed-trial comparison with uncertainty and limitations.";
    }
    return "Run an analysis to calculate descriptive genotype summaries from the observed trial data.";
  })();
  return (
    <article
      className={`card evidence-card${section === "genotype-explorer" ? " genotype-explorer-card" : ""}${section === "trait-analytics" ? " trait-analytics-card" : ""}${section === "environments" ? " environments-card" : ""}`}
      id="evidence"
    >
      <div className="card-head">
        <span className="eyebrow">EVIDENCE VIEW</span>
        <span className="evidence-count">{artifacts.length} ARTIFACTS</span>
      </div>
      <h2>{resultsTitle(section)}</h2>
      {report && report.completion_status !== "complete" && (
        <output className="notice result-notice">
          Partial report: requested analyses remain incomplete. Review the saved
          evidence and limitations before interpreting these results.
        </output>
      )}
      <div className="evidence-topics" aria-label="Evidence topics">
        <span>GENOTYPE SUMMARIES</span>
        <span>TRAIT ANALYSIS</span>
        <span>ENVIRONMENT COMPARISON</span>
      </div>
      {retrieving && (
        <output
          className="evidence-retrieval-skeleton"

          aria-label="Retrieving persisted experiment results"
        >
          <span className="sr-only">
            Retrieving persisted experiment results
          </span>
          <span className="skeleton skeleton-line" />
          <span className="skeleton skeleton-result" />
          <span className="skeleton skeleton-line skeleton-line-short" />
        </output>
      )}
      {!retrieving && !hasAnyRequestedArtifact && (
        <EmptyState
          compact
          icon="evidence"
          title={renderedChoice1}
          description={renderedChoice2}
          action={
            <Link className="primary-link" href="/experiment-studio">
              Start an experiment <span aria-hidden="true">↗</span>
            </Link>
          }
        />
      )}
      {showContrast && contrast && (
        <ContrastResult
          artifact={contrast}
          results={resultValues}
          means={means}
          interval={contrastCI}
          formatNumber={formatNumber}
        />
      )}
      {showContrast && contrast && showRanking && !ranking && (
        <EmptyState
          compact
          icon="evidence"
          title="No genotype summaries yet"
          description="This saved run includes a regime comparison but no genotype summary artifact."
          action={
            <Link className="text-link" href="/experiment-studio">
              Start a new experiment ↗
            </Link>
          }
        />
      )}
      {showRanking && (
        <GenotypeResults
          ranking={ranking}
          genotypes={topGenotypes}
          showContrast={showContrast}
          hasContrast={Boolean(contrast)}
        />
      )}
      <EvidenceExports
        report={report}
        artifacts={artifacts}
        events={events}
        downloadFile={downloadFile}
      />
    </article>
  );
}
