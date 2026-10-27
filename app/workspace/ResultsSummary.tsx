import { MetricVisual, GenotypeMiniPlot } from "./EvidenceVisualizations";
import { finiteMeasure } from "./ResultInterval";
import { ResultIcon } from "./ResultIcon";
import type { ResearchArtifact, ResearchReport } from "./workspace-types";
import type { ComponentProps, ReactNode } from "react";

type IconName = ComponentProps<typeof ResultIcon>["name"];
function ResultMetric({
  icon,
  label,
  value,
  unit,
  note,
  visual,
}: Readonly<{
  icon: IconName;
  label: string;
  value: string;
  unit?: string;
  note: string;
  visual?: ReactNode;
}>) {
  return (
    <div className="result-metric">
      <dt>
        <ResultIcon name={icon} />
        {label}
      </dt>
      <dd>
        {value}
        {unit && <span>{unit}</span>}
        <small>{note}</small>
        {visual}
      </dd>
    </div>
  );
}
export function ResultsSummary({
  contrast,
  ranking,
  formatNumber,
}: Readonly<{
  contrast?: ResearchArtifact;
  ranking?: ResearchArtifact;
  formatNumber: (value: unknown) => string;
}>) {
  const means = contrast?.results.mean_yield_by_regime as
    Record<string, unknown> | undefined;
  const counts = contrast?.results.plot_count_by_regime as
    Record<string, unknown> | undefined;
  const genotypes = Array.isArray(ranking?.results.genotypes)
    ? ranking.results.genotypes
    : undefined;
  const maximum = Math.max(
    finiteMeasure(means?.DROUGHT) ?? 0,
    finiteMeasure(means?.WELL_WATERED) ?? 0,
    1,
  );
  return (
    <dl className="results-metric-strip" aria-label="Measured result summary">
      <ResultMetric
        icon="comparison"
        visual={
          <MetricVisual
            value={means?.DROUGHT}
            maximum={maximum}
            description="Managed drought mean yield, kg/ha"
          />
        }
        label="Managed drought"
        value={formatNumber(means?.DROUGHT)}
        unit="kg/ha"
        note={
          counts?.DROUGHT
            ? `${formatNumber(counts.DROUGHT)} observed plots`
            : "No regime contrast in this run"
        }
      />
      <ResultMetric
        icon="plots"
        visual={
          <MetricVisual
            value={means?.WELL_WATERED}
            maximum={maximum}
            description="Well-watered mean yield, kg/ha"
          />
        }
        label="Well-watered"
        value={formatNumber(means?.WELL_WATERED)}
        unit="kg/ha"
        note={
          counts?.WELL_WATERED
            ? `${formatNumber(counts.WELL_WATERED)} observed plots`
            : "No regime contrast in this run"
        }
      />
      <ResultMetric
        icon="retention"
        visual={
          <MetricVisual
            value={
              contrast?.results.drought_to_well_watered_yield_ratio_percent
            }
            maximum={100}
            reference={100}
            description="Observed yield retention, percent"
          />
        }
        label="Descriptive yield retention"
        value={formatNumber(
          contrast?.results.drought_to_well_watered_yield_ratio_percent,
        )}
        unit="%"
        note="Drought mean / well-watered mean"
      />
      <ResultMetric
        icon="genotype"
        visual={genotypes ? <GenotypeMiniPlot entries={genotypes} /> : null}
        label="Genotypes summarized"
        value={genotypes ? genotypes.length.toLocaleString() : "—"}
        note={
          ranking
            ? `${formatNumber(ranking.sample_size)} drought plot records`
            : "No genotype summaries in this run"
        }
      />
    </dl>
  );
}
export function ResultsProvenance({
  report,
  artifacts,
}: Readonly<{ report: ResearchReport | null; artifacts: ResearchArtifact[] }>) {
  const source = report?.source_sha256 ?? artifacts[0]?.source_sha256;
  if (!source) return null;
  return (
    <details className="results-provenance">
      <summary>
        <ResultIcon name="source" />
        <span>Trace this result to its source</span>
        <code>{source.slice(0, 12)}…</code>
      </summary>
      <div>
        <p>
          Ghana / WACCI combined field trials · Abu et al. (2026) · CC BY 4.0
        </p>
        <a
          href="https://doi.org/10.5281/zenodo.22666201"
          target="_blank"
          rel="noreferrer"
        >
          Dataset DOI 10.5281/zenodo.22666201 ↗
        </a>
        <p>Immutable source SHA-256</p>
        <code className="hash">{source}</code>
        {report && (
          <p>
            Run {report.run_id} · seed {report.seed} · {report.replay_label}
          </p>
        )}
      </div>
    </details>
  );
}
