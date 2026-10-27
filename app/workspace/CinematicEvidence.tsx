import type { ResearchArtifact } from "./workspace-types";
import {
  ExtendedEvidence,
  extendedArtifactsForSection,
} from "./ExtendedEvidence";
import { ResultIcon } from "./ResultIcon";
import { ResultInterval, finiteMeasure } from "./ResultInterval";

export const cinematicNumber = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: 1 })
    : "—";

export function CinematicEvidence({
  artifacts,
}: Readonly<{ artifacts: ResearchArtifact[] }>) {
  const extended = extendedArtifactsForSection(artifacts, "research-results");
  const contrast = artifacts.find(
    (artifact) => artifact.tool_name === "compare_regimes",
  );
  const ranking = artifacts.find(
    (artifact) => artifact.tool_name === "rank_genotypes",
  );
  const interval = contrast?.uncertainty?.yield_difference_95_ci_kg_ha;
  const bounds = Array.isArray(interval) ? interval : [];
  const entries = Array.isArray(ranking?.results.genotypes)
    ? (ranking.results.genotypes as Array<Record<string, unknown>>)
    : [];
  const top = entries.slice(0, 3);
  const largest = Math.max(
    1,
    ...top.map(
      (entry) => finiteMeasure(entry.equal_environment_mean_yield_kg_ha) ?? 0,
    ),
  );
  return (
    <section
      className="cinema-evidence"
      aria-label="Evidence revealed at this event"
    >
      <div className="cinema-panel-label">
        <ResultIcon name="interval" /> RECORDED EVIDENCE · {artifacts.length}{" "}
        artifacts
      </div>
      {contrast ? (
        <div className="cinema-result-reveal" key={contrast.artifact_id}>
          <h3>Observed yield contrast</h3>
          <p className="cinema-estimate">
            {cinematicNumber(contrast.results.yield_difference_kg_ha)}{" "}
            <span>kg/ha</span>
          </p>
          <p className="caption">
            Managed drought minus well-watered · n = {contrast.sample_size}
          </p>
          <p className="caption">
            Water regime and trial environment are confounded. This observed
            contrast does not isolate a causal irrigation effect.
          </p>
          <ResultInterval
            estimate={contrast.results.yield_difference_kg_ha}
            interval={contrast.uncertainty?.yield_difference_95_ci_kg_ha}
            formatNumber={cinematicNumber}
          />
          <p className="caption">
            95% block-bootstrap interval: {cinematicNumber(bounds[0])} to{" "}
            {cinematicNumber(bounds[1])} kg/ha · recorded seed{" "}
            {cinematicNumber(contrast.uncertainty?.seed)}
          </p>
        </div>
      ) : (
        extended.length === 0 && (
          <div className="cinema-awaiting">
            <ResultIcon name="record" />
            <h3>Evidence arrives with the record.</h3>
            <p>
              Measurements appear only after their saved tool-completion event.
              Playback does not run an analysis.
            </p>
          </div>
        )
      )}
      <ExtendedEvidence artifacts={extended} />
      {top.length > 0 && (
        <div
          className="cinema-candidates cinema-result-reveal"
          key={ranking?.artifact_id}
        >
          <h3>Leading observed drought means</h3>
          <ol>
            {top.map((entry) => (
              <li key={String(entry.genotype_id)}>
                <span>{String(entry.genotype_id)}</span>
                <strong>
                  {cinematicNumber(entry.equal_environment_mean_yield_kg_ha)}{" "}
                  <small>kg/ha</small>
                </strong>
                <span className="cinema-candidate-track" aria-hidden="true">
                  <span
                    style={{
                      width: `${Math.max(0, ((finiteMeasure(entry.equal_environment_mean_yield_kg_ha) ?? 0) / largest) * 100)}%`,
                    }}
                  />
                </span>
              </li>
            ))}
          </ol>
          <p className="caption">
            Descriptive equal-environment means. Ranking uncertainty was not
            estimated. These are candidates for research, not field
            recommendations.
          </p>
        </div>
      )}
    </section>
  );
}
