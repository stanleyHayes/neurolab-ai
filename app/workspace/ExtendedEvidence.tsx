"use client";
import { useState } from "react";
import {
  TraitAssociationPlot,
  EnvironmentYieldPlot,
} from "./EvidenceVisualizations";
import { ResultIcon } from "./ResultIcon";
import { finiteMeasure } from "./ResultInterval";
import type { ResearchArtifact, WorkspaceSection } from "./workspace-types";

type Row = Record<string, unknown>;
const rows = (value: unknown): Row[] =>
  Array.isArray(value)
    ? value.filter((item) => item && typeof item === "object")
    : [];
const record = (value: unknown): Row =>
  value && typeof value === "object" ? (value as Row) : {};
const numeric = (value: unknown, digits = 1) =>
  finiteMeasure(value)?.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  }) ?? "—";
const identifier = (value: unknown) =>
  typeof value === "string" ? value : "Not recorded";
const label = (value: unknown) =>
  typeof value === "string" ? value.replaceAll("_", " ") : "Not recorded";

export function extendedArtifactsForSection(
  artifacts: ResearchArtifact[],
  section: WorkspaceSection,
) {
  const names: string[] = [];
  if (section === "trait-analytics" || section === "research-results")
    names.push("analyze_trait_associations");
  if (section === "environments" || section === "research-results")
    names.push("summarize_environment_stability");
  return artifacts.filter((artifact) => names.includes(artifact.tool_name));
}
function CorrelationCell({ value }: Readonly<{ value: unknown }>) {
  const amount = finiteMeasure(value);
  const intensity = amount === null ? 0 : Math.min(1, Math.abs(amount));
  return (
    <td
      className="association-cell"
      style={{
        backgroundColor: `rgb(${amount !== null && amount < 0 ? "205 154 87" : "101 172 143"} / ${intensity * 0.32})`,
      }}
    >
      {numeric(value, 3)}
    </td>
  );
}
function TraitEvidence({ artifact }: Readonly<{ artifact: ResearchArtifact }>) {
  const associations = rows(artifact.results.associations);
  const environments = rows(associations[0]?.per_environment).map((item) =>
    identifier(item.environment_code),
  );
  return (
    <section
      className="results-panel extended-evidence"
      aria-label="Observed drought trait associations"
    >
      <span className="results-overline">
        <ResultIcon name="genotype" /> EXPLORATORY TRAIT ASSOCIATIONS
      </span>
      <h3>Characteristics associated with observed drought yield.</h3>
      <p>
        One equal-environment mean per genotype. Cells show Spearman rank
        correlation (−1 to +1), with average ranks for ties. The final column
        gives a conditional genotype-resampling interval, not validated
        population coverage.
      </p>
      <TraitAssociationPlot associations={associations} />
      <section
        className="results-table-scroll"
        aria-label="Trait association table"
      >
        <table className="extended-evidence-table">
          <caption>
            Spearman association with grain yield (kg/ha); genotype units, not
            independent plot replicates
          </caption>
          <thead>
            <tr>
              <th scope="col">Trait / unit</th>
              <th scope="col">Genotypes</th>
              <th scope="col">Across observed environments</th>
              {environments.map((env) => (
                <th scope="col" key={env}>
                  {env}
                </th>
              ))}
              <th scope="col">95% resampling interval</th>
            </tr>
          </thead>
          <tbody>
            {associations.map((association) => (
              <tr key={String(association.trait)}>
                <th scope="row">
                  {label(association.trait)}
                  <small>{label(association.unit)}</small>
                </th>
                <td>{numeric(association.genotype_count, 0)}</td>
                <CorrelationCell value={association.spearman_rho} />
                {rows(association.per_environment).map((env) => (
                  <CorrelationCell
                    key={String(env.environment_code)}
                    value={env.spearman_rho}
                  />
                ))}
                <td>
                  {Array.isArray(
                    association.spearman_rho_95_percentile_interval,
                  )
                    ? association.spearman_rho_95_percentile_interval
                        .map((value) => numeric(value, 3))
                        .join(" to ")
                    : "Not estimated"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="caption">
        Negative values: larger trait values accompany lower observed yields.
        Positive values: they accompany higher observed yields. Color indicates
        sign and magnitude; all numeric values are printed. A missing value is
        not a zero association.
      </p>
      <p className="caption">
        Seven exploratory traits are compared without multiplicity correction.
        Stay-green score direction is unverified. Correlation does not establish
        a causal trait effect.
      </p>
      <EvidenceLimits artifact={artifact} />
    </section>
  );
}
function rankRange(value: unknown): string {
  const ranks = Object.values(record(value))
    .map(finiteMeasure)
    .filter((rank): rank is number => rank !== null);
  return ranks.length
    ? `${numeric(Math.min(...ranks), 1)}–${numeric(Math.max(...ranks), 1)}`
    : "Not estimated";
}
function EnvironmentEvidence({
  artifact,
}: Readonly<{ artifact: ResearchArtifact }>) {
  const [expanded, setExpanded] = useState(false);
  const regimes = record(artifact.results.regimes);
  return (
    <section
      className="results-panel extended-evidence"
      aria-label="Observed environment yield sensitivity"
    >
      <span className="results-overline">
        <ResultIcon name="comparison" /> OBSERVED ENVIRONMENT SENSITIVITY
      </span>
      <h3>How much do observed means and ranks vary?</h3>
      <p>
        Regimes are analyzed separately. Environment means have equal weight. SD
        measures observed variation in kg/ha; the centered SD removes the
        average observed environment level. Leaving one environment out tests
        rank sensitivity, not future adaptation.
      </p>
      {Object.entries(regimes).map(([regime, value]) => {
        const data = record(value);
        const entries = rows(data.genotypes);
        const shown = expanded ? entries : entries.slice(0, 8);
        const envs = Array.isArray(data.environment_codes)
          ? data.environment_codes
          : [];
        return (
          <div className="environment-sensitivity-block" key={regime}>
            <h4>
              {label(regime)} · {numeric(data.complete_genotype_count, 0)}{" "}
              genotypes with complete coverage
            </h4>
            <EnvironmentYieldPlot
              entries={entries}
              environments={envs}
              regime={regime}
            />
            <section
              className="results-table-scroll"
              aria-label={`${label(regime)} environment means`}
            >
              <table className="extended-evidence-table">
                <caption>
                  Observed grain yield in kg/ha · {shown.length} of{" "}
                  {entries.length} genotype summaries
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Genotype</th>
                    {envs.map((env) => (
                      <th scope="col" key={String(env)}>
                        {identifier(env)}
                      </th>
                    ))}
                    <th scope="col">Mean</th>
                    <th scope="col">SD</th>
                    <th scope="col">Centered SD</th>
                    <th scope="col">Omitted-environment rank range</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.map((entry) => (
                    <tr key={String(entry.genotype_id)}>
                      <th scope="row">
                        {identifier(entry.genotype_id)}
                        {!entry.complete_environment_coverage && (
                          <small>Incomplete environment coverage</small>
                        )}
                      </th>
                      {envs.map((env) => (
                        <td key={String(env)}>
                          {numeric(
                            rows(entry.environment_means).find(
                              (point) => point.environment_code === env,
                            )?.mean_yield_kg_ha,
                          )}
                        </td>
                      ))}
                      <td>{numeric(entry.mean_yield_kg_ha)}</td>
                      <td>{numeric(entry.environment_mean_sd_kg_ha)}</td>
                      <td>{numeric(entry.environment_centered_sd_kg_ha)}</td>
                      <td>
                        {rankRange(entry.leave_one_environment_out_ranks)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
      })}
      <button
        type="button"
        className="secondary-button"
        onClick={() => setExpanded((value) => !value)}
      >
        {expanded
          ? "Show leading environment summaries"
          : "Show every environment summary"}
      </button>
      <p className="caption">
        Rows follow observed mean yield, not a validated stability score. Low
        variation does not by itself imply high yield or tolerance. Incomplete
        genotypes do not receive comparison ranks.
      </p>
      <EvidenceLimits artifact={artifact} />
    </section>
  );
}
function EvidenceLimits({
  artifact,
}: Readonly<{ artifact: ResearchArtifact }>) {
  return (
    <details className="extended-method-limits">
      <summary>Method limits and source evidence</summary>
      <ul>
        {artifact.warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
      <p>
        {artifact.analysis_version} · evidence {artifact.artifact_id}
      </p>
      <code>{artifact.source_sha256}</code>
    </details>
  );
}
export function ExtendedEvidence({
  artifacts,
}: Readonly<{ artifacts: ResearchArtifact[] }>) {
  return (
    <>
      {artifacts.map((artifact) =>
        artifact.tool_name === "analyze_trait_associations" ? (
          <TraitEvidence key={artifact.artifact_id} artifact={artifact} />
        ) : (
          <EnvironmentEvidence key={artifact.artifact_id} artifact={artifact} />
        ),
      )}
    </>
  );
}
