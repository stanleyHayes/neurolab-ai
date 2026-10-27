import { Skeleton } from "./Skeleton";
import type { DatasetProfile, ResearchReport } from "./workspace-types";

type SourceProvenanceProps = {
  profile: DatasetProfile | null;
  profileLoading: boolean;
  report: ResearchReport | null;
};

function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: 0 })
    : "—";
}

export function SourceProvenance({
  profile,
  profileLoading,
  report,
}: Readonly<SourceProvenanceProps>) {
  return (
    <article
      className="card provenance-card"
      id="provenance"
      aria-busy={profileLoading}
    >
      <div className="card-head">
        <span className="eyebrow">SOURCE DATA</span>
      </div>
      <h2>Source provenance</h2>
      <div className="dataset-name">Ghana combined · maize phenotypes</div>
      <div className="metric-row">
        <div className="metric">
          <strong>
            {profileLoading ? (
              <Skeleton className="skeleton-number" />
            ) : (
              formatNumber(profile?.row_count)
            )}
          </strong>
          <span>plot records</span>
        </div>
        <div className="metric">
          <strong>
            {profileLoading ? (
              <Skeleton className="skeleton-number" />
            ) : (
              formatNumber(profile?.genotype_count)
            )}
          </strong>
          <span>genotypes</span>
        </div>
      </div>
      <a
        className="doi"
        href="https://doi.org/10.5281/zenodo.22666201"
        target="_blank"
        rel="noreferrer"
      >
        Abu et al. (2026) · Zenodo DOI ↗
      </a>
      <p className="caption">
        CC BY 4.0 · Source authors do not endorse these interpretations. Water
        regimes are confounded with trial environments. ENVT indices are not
        calendar years.
      </p>
      <div className="hash-label">CURRENT SOURCE SHA-256</div>
      {profileLoading ? (
        <Skeleton className="skeleton-hash" />
      ) : (
        <code className="hash">{profile?.source_sha256 ?? "—"}</code>
      )}
      {report && (
        <>
          <div className="hash-label">RUN SOURCE SHA-256</div>
          <code className="hash">{report.source_sha256}</code>
        </>
      )}
    </article>
  );
}
