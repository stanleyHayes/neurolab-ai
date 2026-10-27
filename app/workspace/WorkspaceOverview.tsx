"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { FallbackIllustration } from "../maize-scene-illustration";
import { Skeleton } from "./Skeleton";
import type { DatasetProfile } from "./workspace-types";

const MaizeSceneCanvas = dynamic(() => import("../maize-scene"), {
  ssr: false,
  loading: () => <FallbackIllustration />,
});

type WorkspaceOverviewProps = {
  profile: DatasetProfile | null;
  profileLoading: boolean;
  runStatus: string;
  busy: boolean;
  reducedMotion: boolean;
};

function formatNumber(value: unknown, digits = 1): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : "—";
}

export function WorkspaceOverview({
  profile,
  profileLoading,
  runStatus,
  busy,
  reducedMotion,
}: Readonly<WorkspaceOverviewProps>) {
  const regimeCount = profile?.water_regimes
    ? Object.keys(profile.water_regimes).length
    : 0;

  const renderedChoice1 = (() => {
    if (profileLoading) {
      return <Skeleton className="skeleton-number" />;
    }
    if (regimeCount) {
      return String(regimeCount).padStart(2, "0");
    }
    return "—";
  })();
  return (
    <>
      <section className="overview-intro" id="overview">
        <div className="kicker">✧ NEUROLAB RESEARCH LABORATORY / 2026</div>
        <div className="heading">
          <div>
            <h1>
              Scientific intelligence,
              <br />
              made visible.
            </h1>
            <p>
              Explore real maize field trials, run reproducible analyses, and
              let research agents plan the next question.
            </p>
          </div>
          <span className="concept-date">GHANA · FIELD EVIDENCE</span>
        </div>
      </section>

      <section className="hero-card" aria-labelledby="hero-title">
        <div className="hero-copy">
          <span className="hero-pill">
            ✦ OBSERVATIONAL AGRICULTURAL RESEARCH
          </span>
          <h2 id="hero-title">
            From field data to
            <br />
            <em>scientific discovery.</em>
          </h2>
          <p>
            One laboratory for drought resilience, genotype performance and
            evidence-led experimentation.
          </p>
          <div className="hero-actions">
            <Link className="primary-link" href="/experiment-studio">
              Start an experiment <span aria-hidden="true">↗</span>
            </Link>
            <Link className="secondary-link" href="/research-results">
              Explore evidence
            </Link>
          </div>
        </div>
        <div
          className="hero-art"
          aria-label="Illustrative maize plant and root structure; not measured crop morphology"
        >
          <div className="art-orbit art-orbit-one" />
          <div className="art-orbit art-orbit-two" />
          <div className="scene-context-label">
            <span className="scene-context-index">
              STRUCTURE / ILLUSTRATIVE
            </span>
            <span>Leaves · stalk · roots</span>
          </div>
          {reducedMotion ? (
            <FallbackIllustration />
          ) : (
            <MaizeSceneCanvas reducedMotion={false} />
          )}
          <span className="art-caption">
            <span className="art-caption-dot" /> ILLUSTRATIVE PLANT MODEL
          </span>
        </div>
      </section>

      <section
        className="stats-strip"
        aria-label="Live dataset profile"
        aria-busy={profileLoading}
      >
        <div className="stat">
          <span>OBSERVATIONS</span>
          <strong>
            {profileLoading ? (
              <Skeleton className="skeleton-number" />
            ) : (
              formatNumber(profile?.row_count, 0)
            )}
          </strong>
          <small>Ghana combined trial records</small>
        </div>
        <div className="stat">
          <span>GENOTYPES</span>
          <strong>
            {profileLoading ? (
              <Skeleton className="skeleton-number" />
            ) : (
              formatNumber(profile?.genotype_count, 0)
            )}
          </strong>
          <small>Distinct study accessions</small>
        </div>
        <div className="stat">
          <span>WATER REGIMES</span>
          <strong>{renderedChoice1}</strong>
          <small>Observed source groups</small>
        </div>
        <div className="stat">
          <span>RUN STATUS</span>
          <strong className="stat-status">
            {busy ? runStatus || "QUEUED" : runStatus || "READY"}
          </strong>
          <small>
            {busy
              ? "Backend analysis in progress"
              : "Persistent research workspace"}
          </small>
        </div>
      </section>

      <section
        className="overview-grid"
        aria-label="How the research workspace works"
      >
        <article className="card visualization-card">
          <div className="card-head">
            <span className="eyebrow">A FIELD-TO-EVIDENCE WORKSPACE</span>
            <span className="tiny-dot" aria-hidden="true">
              ●
            </span>
          </div>
          <h2>Make each result traceable.</h2>
          <p className="overview-copy">
            Start with an observational question. Every computation is attached
            to its source, method, uncertainty and limitations.
          </p>
          <Link className="text-link" href="/data-library">
            Inspect source provenance <span aria-hidden="true">↗</span>
          </Link>
        </article>
        <article className="card workflow-card" id="workflow">
          <div className="card-head">
            <span className="eyebrow">EXPERIMENT PIPELINE</span>
            <span className="tiny-dot" aria-hidden="true">
              ●
            </span>
          </div>
          <h2>Research workflow</h2>
          <ol className="workflow-list">
            <li>
              <span>01</span>
              <div>
                <strong>Ask</strong>
                <small>State a scientific question</small>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <strong>Plan</strong>
                <small>Choose a bounded analysis mode</small>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <strong>Compute</strong>
                <small>Validated tools analyze observations</small>
              </div>
            </li>
            <li>
              <span>04</span>
              <div>
                <strong>Verify</strong>
                <small>Review evidence and provenance</small>
              </div>
            </li>
          </ol>
        </article>
      </section>
    </>
  );
}
