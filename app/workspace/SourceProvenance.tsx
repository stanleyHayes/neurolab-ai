"use client";
import { useState } from "react";
import { Skeleton } from "./Skeleton";
import { ResultIcon } from "./ResultIcon";
import type { DatasetProfile, ResearchReport } from "./workspace-types";

type SourceProvenanceProps = {
  profile: DatasetProfile | null;
  profileLoading: boolean;
  report: ResearchReport | null;
};
const formatNumber = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: 0 })
    : "—";

export function SourceProvenance({
  profile,
  profileLoading,
  report,
}: Readonly<SourceProvenanceProps>) {
  const [copyStatus, setCopyStatus] = useState("");
  const mismatch = Boolean(
    profile && report && profile.source_sha256 !== report.source_sha256,
  );
  const regimes = Object.entries(profile?.water_regimes ?? {});
  async function copyHash() {
    if (!profile?.source_sha256) return;
    try {
      await navigator.clipboard.writeText(profile.source_sha256);
      setCopyStatus("Source hash copied.");
    } catch {
      setCopyStatus(
        "Copy is unavailable. Select the source hash below to copy it manually.",
      );
    }
  }
  const metrics = [
    { label: "Plot records", value: profile?.row_count, icon: "plots" },
    { label: "Genotypes", value: profile?.genotype_count, icon: "genotype" },
    {
      label: "ENVT indices",
      value: profile?.year_codes?.length,
      icon: "comparison",
    },
  ] as const;
  const status = profileLoading ? "LOADING SOURCE" : "SOURCE UNAVAILABLE";
  return (
    <article
      className="card provenance-card source-workbench"
      id="provenance"
      aria-busy={profileLoading}
    >
      <div className="source-overview">
        <header className="source-header">
          <div>
            <span className="results-overline">
              <ResultIcon name="source" /> SOURCE DATA
            </span>
            <h2>Ghana maize trials</h2>
            <p>Combined phenotypes · source provenance</p>
          </div>
          <span className="source-loaded">
            <ResultIcon name={profile ? "complete" : "record"} />
            {profile && !profileLoading ? "SOURCE LOADED" : status}
          </span>
        </header>
        <dl className="source-metrics" aria-label="Source dataset counts">
          {metrics.map((metric) => (
            <div key={metric.label}>
              <dt>
                <ResultIcon name={metric.icon} />
                {metric.label}
              </dt>
              <dd>
                {profileLoading ? (
                  <Skeleton className="skeleton-number" />
                ) : (
                  formatNumber(metric.value)
                )}
              </dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="source-detail-grid">
        <section
          className="source-citation"
          aria-label="Original study citation"
        >
          <span className="source-section-label">
            <ResultIcon name="record" /> ORIGINAL STUDY
          </span>
          <h3>Original study & attribution</h3>
          <a
            className="source-study-link"
            href="https://doi.org/10.5281/zenodo.22666201"
            target="_blank"
            rel="noreferrer"
          >
            <span>
              <strong>Abu et al. (2026)</strong>
              <small>Zenodo · DOI 10.5281/zenodo.22666201</small>
            </span>
            <ResultIcon name="arrow" />
          </a>
          <div className="source-license">
            <span>CC BY 4.0</span>
            <p>Source authors do not endorse these interpretations.</p>
          </div>
          <div className="source-regimes">
            <span className="source-section-label">OBSERVED WATER REGIMES</span>
            {regimes.length ? (
              <ul>
                {regimes.map(([regime, count]) => (
                  <li key={regime}>
                    <span>{regimeLabel(regime)}</span>
                    <strong>
                      {formatNumber(count)} <small>plots</small>
                    </strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="caption">Regime counts are not available.</p>
            )}
          </div>
        </section>
        <section className="source-identity" aria-label="Source file identity">
          <div className="source-identity-heading">
            <span className="source-section-label">
              <ResultIcon name="source" /> FILE IDENTITY
            </span>
            <button
              className="text-button"
              type="button"
              onClick={() => void copyHash()}
              disabled={profileLoading || !profile?.source_sha256}
            >
              <ResultIcon name="copy" /> Copy source hash
            </button>
          </div>
          <h3>Source fingerprint</h3>
          <p className="caption">
            The SHA-256 identifies the exact source bytes used by the analysis.
          </p>
          <span className="source-hash-label">CURRENT SOURCE SHA-256</span>
          {profileLoading ? (
            <Skeleton className="skeleton-hash" />
          ) : (
            <code className="source-hash">
              {profile?.source_sha256 ?? "Source identity unavailable"}
            </code>
          )}
          <output className="source-copy-status">{copyStatus}</output>
          {report && (
            <div
              className={`source-run-match${mismatch ? " source-run-mismatch" : ""}`}
            >
              <ResultIcon name={mismatch ? "caution" : "record"} />
              <div>
                <strong>{runSourceLabel(profile, mismatch)}</strong>
                {(mismatch || !profile) && (
                  <code className="source-hash">{report.source_sha256}</code>
                )}
                <span>Selected run {report.run_id.slice(0, 8)}</span>
              </div>
            </div>
          )}
        </section>
      </div>
      <div className="source-science-note">
        <ResultIcon name="caution" />
        <div>
          <strong>Interpretation boundaries</strong>
          <p>
            Water regime is confounded with trial environment. ENVT indices are
            not calendar years. The combined source and its regime-specific
            components must not be counted as independent observations.
          </p>
        </div>
      </div>
    </article>
  );
}
function runSourceLabel(
  profile: DatasetProfile | null,
  mismatch: boolean,
): string {
  if (!profile) return "Run source recorded; current source unavailable";
  return mismatch
    ? "Selected run uses a different source"
    : "Selected run matches this source";
}

function regimeLabel(regime: string): string {
  const labels: Record<string, string> = {
    DROUGHT: "Managed drought",
    WELL_WATERED: "Well-watered",
  };
  return labels[regime] ?? regime;
}
