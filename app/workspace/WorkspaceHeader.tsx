"use client";

import Link from "next/link";
import type { RefObject } from "react";

type WorkspaceHeaderProps = {
  title: string;
  providerLabel: string;
  runId: string;
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
  account,
  isOverview,
  sidebarCollapsed,
  setSidebarCollapsed,
  mobileNavOpen,
  setMobileNavOpen,
  mobileNavTriggerRef,
}: Readonly<WorkspaceHeaderProps>) {
  return (
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
        <span className="breadcrumb">NEUROLAB / {title.toUpperCase()}</span>
      </div>
      <div className="topbar-actions">
        <span className="research-mode">
          <span className="mode-dot" aria-hidden="true" /> RESEARCH MODE
        </span>
        <span className="top-provider">{providerLabel}</span>
        {runId && <span className="run-id">RUN {runId.slice(0, 8)}</span>}
        <Link
          className="account-chip"
          href="/settings/account"
          aria-label={`Account settings for ${account?.display_name ?? "researcher"}`}
        >
          <span className="avatar" aria-hidden="true">
            {account?.display_name.slice(0, 2).toUpperCase() ?? "NL"}
          </span>
          <span>{account?.display_name ?? "Account"}</span>
        </Link>
      </div>
    </header>
  );
}
