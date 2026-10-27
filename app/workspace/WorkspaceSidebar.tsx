"use client";

import Link from "next/link";
import Image from "next/image";
import { ResultIcon } from "./ResultIcon";

const navigationIcons = {
  overview: "plots",
  "experiment-studio": "method",
  "live-experiment": "retention",
  "research-results": "evidence",
  "genotype-explorer": "genotype",
  "trait-analytics": "comparison",
  environments: "plots",
  "data-library": "source",
  "ai-insights": "spark",
  "next-experiments": "arrow",
  reports: "record",
  settings: "settings",
} as const;
import type { Dispatch, RefObject, SetStateAction } from "react";
import { WORKSPACE_NAV_GROUPS } from "./workspace-config";
import type { WorkspaceSection } from "./workspace-types";

type WorkspaceSidebarProps = {
  section: WorkspaceSection;
  collapsedNavGroups: string[];
  toggleNavGroup: (groupId: string) => void;
  sidebarRef: RefObject<HTMLElement | null>;
  isMobileViewport: boolean;
  mobileNavOpen: boolean;
  setMobileNavOpen: Dispatch<SetStateAction<boolean>>;
  mobileNavCloseRef: RefObject<HTMLButtonElement | null>;
  mobileNavTriggerRef: RefObject<HTMLButtonElement | null>;
};

export function WorkspaceSidebar({
  section,
  collapsedNavGroups,
  toggleNavGroup,
  sidebarRef,
  isMobileViewport,
  mobileNavOpen,
  setMobileNavOpen,
  mobileNavCloseRef,
  mobileNavTriggerRef,
}: Readonly<WorkspaceSidebarProps>) {
  const closeNavigation = () => {
    setMobileNavOpen(false);
    mobileNavTriggerRef.current?.focus();
  };

  const NavigationSurface = isMobileViewport ? "dialog" : "aside";

  return (
    <>
      <NavigationSurface
        className="sidebar"
        id="primary-navigation"
        ref={(element) => {
          sidebarRef.current = element;
        }}
        open={isMobileViewport ? mobileNavOpen : undefined}
        aria-modal={isMobileViewport && mobileNavOpen ? true : undefined}
        aria-label="Primary navigation"
        aria-hidden={isMobileViewport && !mobileNavOpen}
        inert={isMobileViewport && !mobileNavOpen}
      >
        <div className="sidebar-brand-row">
          <Link
            className="brand"
            href="/"
            aria-label="NeuroLab AI overview"
            onClick={closeNavigation}
          >
            <Image
              className="brand-full-lockup"
              src="/brand/04_full_horizontal.svg"
              alt="NeuroLab AI — Discover. Experiment. Impact."
              width={1800}
              height={550}
              priority
              unoptimized
            />
            <Image
              className="brand-symbol-lockup"
              src="/brand/01_logo_only.svg"
              alt=""
              aria-hidden="true"
              width={1024}
              height={1024}
              unoptimized
            />
          </Link>
          <button
            ref={mobileNavCloseRef}
            className="mobile-nav-close"
            type="button"
            aria-label="Close navigation menu"
            onClick={closeNavigation}
          >
            <svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">
              <path d="m5 5 10 10M15 5 5 15" />
            </svg>
          </button>
        </div>
        <div className="sidebar-scroll-area">
          <div className="side-label">RESEARCH WORKSPACE</div>
          <nav className="sidebar-nav" aria-label="Research workspace">
            {WORKSPACE_NAV_GROUPS.map((group) => {
              const isCollapsed = collapsedNavGroups.includes(group.id);
              const isActive = group.items.some(
                (item) => item.section === section,
              );
              const groupPanelId = `nav-group-${group.id}`;
              return (
                <section
                  className={`nav-group${isActive ? " nav-group-active" : ""}${isCollapsed ? " nav-group-collapsed" : ""}`}
                  key={group.id}
                >
                  <button
                    className="nav-group-toggle"
                    type="button"
                    aria-expanded={!isCollapsed}
                    aria-controls={groupPanelId}
                    aria-label={`${isCollapsed ? "Expand" : "Collapse"} ${group.label}`}
                    title={group.label}
                    onClick={() => toggleNavGroup(group.id)}
                  >
                    <i className="nav-group-icon" aria-hidden="true">
                      <ResultIcon
                        name={navigationIcons[group.items[0].section]}
                      />
                    </i>
                    <span className="nav-group-label">{group.label}</span>
                    {isActive && (
                      <span className="nav-group-current" aria-hidden="true" />
                    )}
                    <span className="nav-group-chevron" aria-hidden="true">
                      <svg viewBox="0 0 12 12" focusable="false">
                        <path d="m3 4.5 3 3 3-3" />
                      </svg>
                    </span>
                  </button>
                  <div
                    className="nav-group-children"
                    id={groupPanelId}
                    hidden={isCollapsed}
                  >
                    {group.items.map((item) => (
                      <Link
                        className={`nav-child-link${section === item.section ? " active" : ""}`}
                        href={
                          item.section === "overview" ? "/" : `/${item.section}`
                        }
                        aria-label={item.label}
                        title={item.label}
                        aria-current={
                          section === item.section ? "page" : undefined
                        }
                        onClick={closeNavigation}
                        key={item.section}
                      >
                        <i aria-hidden="true">
                          <ResultIcon name={navigationIcons[item.section]} />
                        </i>
                        <span>{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </section>
              );
            })}
          </nav>
          <div className="sidebar-foot">
            <b>Make discovery tangible.</b>
            <p>
              Real evidence. Verifiable experiments. Research that stays
              grounded in the data.
            </p>
          </div>
        </div>
      </NavigationSurface>
      {mobileNavOpen && (
        <button
          className="mobile-nav-backdrop"
          type="button"
          aria-label="Close navigation menu"
          tabIndex={-1}
          onClick={closeNavigation}
        />
      )}
    </>
  );
}
