"use client";

import Link from "next/link";
import { ThemeControl } from "../theme-control";
import { useEffect, useRef } from "react";
import type { RefObject } from "react";
import type { SavedRun } from "./workspace-types";

type WorkspaceHeaderProps = {
  title: string;
  providerLabel: string;
  runId: string;
  savedRuns: SavedRun[];
  onSelectRun: (id: string) => void;
  account: { display_name: string } | null;
  isOverview: boolean;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (update: (collapsed: boolean) => boolean) => void;
  mobileNavOpen: boolean;
  setMobileNavOpen: (update: (open: boolean) => boolean) => void;
  mobileNavTriggerRef: RefObject<HTMLButtonElement | null>;
};

export function WorkspaceHeader({
  title,
  providerLabel,
  runId,
  savedRuns,
  onSelectRun,
  account,
  isOverview,
  sidebarCollapsed,
  setSidebarCollapsed,
  mobileNavOpen,
  setMobileNavOpen,
  mobileNavTriggerRef,
}: Readonly<WorkspaceHeaderProps>) {
  const pickerRef = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const dismissOnEscape = (event: KeyboardEvent) => {
      const picker = pickerRef.current;
      if (event.key !== "Escape" || !picker?.open) return;
      picker.open = false;
      picker.querySelector("summary")?.focus();
    };
    const dismissOutside = (event: Event) => {
      const picker = pickerRef.current;
      if (picker?.open && !picker.contains(event.target as Node))
        picker.open = false;
    };
    document.addEventListener("keydown", dismissOnEscape);
    document.addEventListener("focusin", dismissOutside);
    document.addEventListener("pointerdown", dismissOutside);
    return () => {
      document.removeEventListener("keydown", dismissOnEscape);
      document.removeEventListener("focusin", dismissOutside);
      document.removeEventListener("pointerdown", dismissOutside);
    };
  }, []);
  return (
    <div className="workspace-navigation">
      <header className="topbar">
        <div className="topbar-leading">
          <button
            ref={mobileNavTriggerRef}
            className="mobile-nav-trigger"
            type="button"
            aria-label={
              mobileNavOpen ? "Close navigation menu" : "Open navigation menu"
            }
            aria-expanded={mobileNavOpen}
            aria-controls="primary-navigation"
            onClick={() => setMobileNavOpen((open) => !open)}
          >
            <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
              {mobileNavOpen ? (
                <path d="m5 5 10 10M15 5 5 15" />
              ) : (
                <path d="M3 5h14M3 10h14M3 15h14" />
              )}
            </svg>
          </button>
          {!isOverview && (
            <button
              className="sidebar-collapse-button"
              type="button"
              aria-label={
                sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"
              }
              aria-expanded={!sidebarCollapsed}
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
            >
              <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
                <path d={sidebarCollapsed ? "m6 3 5 5-5 5" : "m10 3-5 5 5 5"} />
              </svg>
            </button>
          )}
          <span className="workspace-heading">
            <small>NEUROLAB</small>
            <span>{title}</span>
          </span>
        </div>
        <div className="topbar-actions">
          <span className="workspace-status" title={providerLabel}>
            <span className="mode-dot" aria-hidden="true" />
            {providerLabel.startsWith("Meta")
              ? "Meta analysis"
              : "Deterministic replay"}
          </span>
          <ThemeControl />
          <Link
            className="account-chip"
            href="/settings/account"
            aria-label={`Account settings for ${account?.display_name ?? "researcher"}`}
          >
            <span className="avatar" aria-hidden="true">
              {account?.display_name
                .split(/\s+/)
                .map((part) => part[0])
                .slice(0, 2)
                .join("")
                .toUpperCase() ?? "NL"}
            </span>
            <span>{account?.display_name ?? "Account"}</span>
          </Link>
        </div>
      </header>
      {savedRuns.length > 0 && (
        <div className="experiment-context">
          <span className="experiment-context-label">EXPERIMENT</span>
          <details className="experiment-picker" key={runId} ref={pickerRef}>
            <summary>
              <span>
                {savedRuns.find((run) => run.run_id === runId)?.objective ??
                  "Choose a saved experiment"}
              </span>
              <svg viewBox="0 0 20 20" aria-hidden="true">
                <path d="m6 8 4 4 4-4" />
              </svg>
            </summary>
            <div className="experiment-options" aria-label="Saved experiments">
              {savedRuns.map((run) => (
                <button
                  type="button"
                  key={run.run_id}
                  aria-label={`Select experiment ${run.run_id.slice(0, 8)}`}
                  aria-current={run.run_id === runId ? "true" : undefined}
                  onClick={(event) => {
                    event.currentTarget
                      .closest("details")
                      ?.removeAttribute("open");
                    onSelectRun(run.run_id);
                  }}
                >
                  <span>{run.objective}</span>
                  <small>
                    {run.status} · {run.run_id.slice(0, 8)}
                  </small>
                </button>
              ))}
            </div>
          </details>
          {runId && (
            <span className="experiment-context-id">{runId.slice(0, 8)}</span>
          )}
        </div>
      )}
    </div>
  );
}
