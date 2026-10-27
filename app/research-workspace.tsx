"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  authenticatedFetch,
  clearAccessToken,
  configureAuthRedirect,
} from "./auth-client";
import type {
  ResearchConfiguration,
  ResearchPlan,
} from "./workspace/research-editor-types";
import { EmptyState } from "./workspace/EmptyState";
import { WorkspaceSidebar } from "./workspace/WorkspaceSidebar";
import { WorkspaceOverview } from "./workspace/WorkspaceOverview";
import { WorkspaceHeader } from "./workspace/WorkspaceHeader";
import { WorkspaceErrorItem } from "./workspace/WorkspaceErrorItem";
import { EvidenceResults } from "./workspace/EvidenceResults";
import { ExperimentSetup } from "./workspace/ExperimentSetup";
import { SourceProvenance } from "./workspace/SourceProvenance";
import { ScientificReportView } from "./workspace/ScientificReportView";
import { ResearchRunPlan } from "./workspace/ResearchRunPlan";
import { ResearchTimeline } from "./workspace/ResearchTimeline";
import { INITIAL_OBJECTIVE, SECTION_COPY } from "./workspace/workspace-config";
import type {
  DatasetProfile,
  ErrorContext,
  ResearchArtifact,
  ResearchEvent,
  ResearchReport,
  SavedRun,
  WorkspaceErrors,
  WorkspaceSection,
} from "./workspace/workspace-types";

const CinematicPlayer = dynamic(
  () =>
    import("./workspace/CinematicPlayer").then(
      (module) => module.CinematicPlayer,
    ),
  { ssr: false },
);

export { WORKSPACE_SECTIONS } from "./workspace/workspace-config";
export type { WorkspaceSection };

function isScientificReportSection(section: WorkspaceSection): boolean {
  return ["reports", "ai-insights"].includes(section);
}

function record(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : {};
}

function text(value: unknown, fallback = "—"): string {
  return typeof value === "string" ? value : fallback;
}

function number(value: unknown, digits = 1): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits })
    : "—";
}

function mergeEvent(
  previous: ResearchEvent[],
  event: ResearchEvent,
): ResearchEvent[] {
  return [
    ...previous.filter((item) => item.sequence !== event.sequence),
    event,
  ].sort((a, b) => a.sequence - b.sequence);
}

function readSessionState(key: string): Record<string, unknown> {
  const saved = window.sessionStorage.getItem(key);
  if (!saved) return {};
  try {
    return record(JSON.parse(saved));
  } catch {
    window.sessionStorage.removeItem(key);
    return {};
  }
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) && value.every((item) => typeof item === "string")
  );
}

async function apiJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(url, {
    ...init,
    cache: "no-store",
  });
  const payload: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = record(payload).detail;
    throw new Error(text(detail, `Request failed (${response.status})`));
  }
  return payload as T;
}

async function consumeEventStream(
  response: Response,
  onEvent: (event: ResearchEvent) => void,
): Promise<void> {
  if (!response.ok || !response.body)
    throw new Error("Could not open the durable event stream.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const line = block
        .split(/\r?\n/)
        .find((entry) => entry.startsWith("data: "));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(6)) as ResearchEvent);
      } catch {
        // Malformed individual event frames are ignored; sequence gaps are visible in history.
      }
    }
    if (done) break;
  }
}

async function consumeRunEvents(
  runId: string,
  onEvent: (event: ResearchEvent) => void,
): Promise<void> {
  let cursor = 0;
  let terminal = false;
  let attempts = 0;
  async function reconnect(): Promise<void> {
    try {
      const response = await authenticatedFetch(
        `/api/research-runs/${encodeURIComponent(runId)}/events?after=${cursor}`,
        { cache: "no-store" },
      );
      await consumeEventStream(response, (event) => {
        cursor = Math.max(cursor, event.sequence);
        onEvent(event);
        terminal ||= [
          "run.completed",
          "run.partial",
          "run.failed",
          "run.timed_out",
          "run.cancelled",
        ].includes(event.event_type);
      });
    } catch (error) {
      if (attempts >= 5) throw error;
    }
    if (!terminal) {
      attempts += 1;
      await new Promise((resolve) =>
        window.setTimeout(resolve, 250 * attempts),
      );
      if (attempts < 6) await reconnect();
    }
  }
  await reconnect();
  if (!terminal)
    throw new Error(
      "Event connection ended before a terminal run event; retry to resume from the last saved cursor.",
    );
}

function downloadFile(filename: string, value: unknown, mime: string): void {
  const blob = new Blob(
    [typeof value === "string" ? value : JSON.stringify(value, null, 2)],
    {
      type: mime,
    },
  );
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(href);
}

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

export function ResearchWorkspace({
  section = "overview",
  children,
  pageTitle,
  accountDisplayName,
}: Readonly<{
  section?: WorkspaceSection;
  children?: ReactNode;
  pageTitle?: string;
  accountDisplayName?: string;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [objective, setObjective] = useState(INITIAL_OBJECTIVE);
  const [events, setEvents] = useState<ResearchEvent[]>([]);
  const [artifacts, setArtifacts] = useState<ResearchArtifact[]>([]);
  const [savedRuns, setSavedRuns] = useState<SavedRun[]>([]);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [errors, setErrors] = useState<WorkspaceErrors>({});
  const [profileLoading, setProfileLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [retryingContext, setRetryingContext] = useState<ErrorContext | null>(
    null,
  );
  const [canceling, setCanceling] = useState(false);
  const [replayLoadingId, setReplayLoadingId] = useState("");
  const [runRetrieving, setRunRetrieving] = useState(false);
  const [runId, setRunId] = useState("");
  const [runStatus, setRunStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [presenting, setPresenting] = useState(false);
  const [mode, setMode] = useState<"replay" | "meta">("replay");
  const [replayIndex, setReplayIndex] = useState(0);
  const [stateRestored, setStateRestored] = useState(false);
  const [account, setAccount] = useState<{
    user_id: string;
    email: string;
    display_name: string;
  } | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [collapsedNavGroups, setCollapsedNavGroups] = useState<string[]>([]);
  const accountId = account?.user_id;
  const restoredFor = useRef("");
  const explicitRunLoad = useRef("");
  const sidebarRef = useRef<HTMLElement>(null);
  const mobileNavTriggerRef = useRef<HTMLButtonElement>(null);
  const mobileNavCloseRef = useRef<HTMLButtonElement>(null);
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 650px)");
    const updateViewport = () => {
      setIsMobileViewport(mediaQuery.matches);
      if (!mediaQuery.matches) setMobileNavOpen(false);
    };

    updateViewport();
    mediaQuery.addEventListener("change", updateViewport);
    return () => mediaQuery.removeEventListener("change", updateViewport);
  }, []);

  useEffect(() => {
    if (!mobileNavOpen || !isMobileViewport) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    mobileNavCloseRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobileNavOpen(false);
        mobileNavTriggerRef.current?.focus();
        return;
      }

      if (event.key !== "Tab" || !sidebarRef.current) return;
      const focusable = Array.from(
        sidebarRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => element.getClientRects().length > 0);
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMobileViewport, mobileNavOpen]);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  const toggleNavGroup = (groupId: string) => {
    setCollapsedNavGroups((current) =>
      current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId],
    );
  };

  useEffect(() => {
    configureAuthRedirect((destination) => router.replace(destination));
  }, [router]);

  useEffect(() => {
    let active = true;
    const restoreAccount = async () => {
      try {
        const response = await authenticatedFetch("/api/auth/me");
        if (!response.ok) throw new Error("Please sign in.");
        const user = (await response.json()) as {
          user_id: string;
          email: string;
          display_name: string;
        };
        if (active) setAccount(user);
      } catch {
        clearAccessToken();
        if (active) {
          const next = `${window.location.pathname}${window.location.search}`;
          router.replace(`/sign-in?next=${encodeURIComponent(next)}`);
        }
      }
    };
    void restoreAccount();
    return () => {
      active = false;
    };
  }, [router]);

  useEffect(() => {
    if (!accountId) return;
    const timer = window.setTimeout(() => {
      window.sessionStorage.removeItem("neurolab-research-state");
      const navigation = readSessionState("neurolab-sidebar-state");
      if (typeof navigation.collapsed === "boolean")
        setSidebarCollapsed(navigation.collapsed);
      if (isStringArray(navigation.collapsedGroups))
        setCollapsedNavGroups(navigation.collapsedGroups);
      const state = readSessionState(`neurolab-research-state:${accountId}`);
      setRunId(typeof state.runId === "string" ? state.runId : "");
      if (typeof state.runStatus === "string") setRunStatus(state.runStatus);
      if (state.mode === "replay" || state.mode === "meta") setMode(state.mode);
      restoredFor.current = accountId;
      setStateRestored(true);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [accountId]);

  useEffect(() => {
    if (!stateRestored || !accountId || restoredFor.current !== accountId)
      return;
    window.sessionStorage.setItem(
      `neurolab-research-state:${accountId}`,
      JSON.stringify({ runId, runStatus, mode }),
    );
  }, [runId, runStatus, mode, stateRestored, accountId]);

  useEffect(() => {
    if (!stateRestored) return;
    window.sessionStorage.setItem(
      "neurolab-sidebar-state",
      JSON.stringify({
        collapsed: sidebarCollapsed,
        collapsedGroups: collapsedNavGroups,
      }),
    );
  }, [sidebarCollapsed, collapsedNavGroups, stateRestored]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      setSavedRuns(await apiJson<SavedRun[]>("/api/research-runs?limit=20"));
      setHistoryLoaded(true);
      setErrors((current) => {
        const next = { ...current };
        delete next.history;
        return next;
      });
    } catch (cause) {
      setHistoryLoaded(true);
      setErrors((current) => ({
        ...current,
        history:
          cause instanceof Error ? cause.message : "Unable to load saved runs.",
      }));
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setErrors((current) => {
      const next = { ...current };
      delete next.dataset;
      return next;
    });
    try {
      setProfile(
        await apiJson<DatasetProfile>("/api/datasets/ghana_combined/profile"),
      );
    } catch (cause) {
      setErrors((current) => ({
        ...current,
        dataset:
          cause instanceof Error
            ? cause.message
            : "Unable to load the Ghana dataset profile.",
      }));
    } finally {
      setProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (pathname !== (section === "overview" ? "/" : `/${section}`) || !runId)
      return;
    if (explicitRunLoad.current === runId) {
      explicitRunLoad.current = "";
      return;
    }
    let active = true;
    const controller = new AbortController();
    setErrors((current) => {
      const next = { ...current };
      delete next.run;
      delete next.failedRun;
      return next;
    });
    const restoreRun = async () => {
      setRunRetrieving(true);
      try {
        const [run, nextArtifacts] = await Promise.all([
          apiJson<{ status: string; report: ResearchReport | null }>(
            `/api/research-runs/${encodeURIComponent(runId)}`,
            { signal: controller.signal },
          ),
          apiJson<ResearchArtifact[]>(
            `/api/research-runs/${encodeURIComponent(runId)}/artifacts`,
            { signal: controller.signal },
          ),
        ]);
        if (!active) return;
        setRunStatus(run.status);
        setReport(run.report);
        setArtifacts(nextArtifacts);
        setBusy(
          ["QUEUED", "RUNNING", "PLANNING", "ANALYZING"].includes(run.status),
        );
        const eventResponse = await authenticatedFetch(
          `/api/research-runs/${encodeURIComponent(runId)}/events?after=0`,
          { cache: "no-store", signal: controller.signal },
        );
        await consumeEventStream(eventResponse, (event) => {
          if (["run.failed", "run.timed_out"].includes(event.event_type)) {
            setErrors((current) => ({
              ...current,
              failedRun: text(
                event.payload.message,
                "The research run failed.",
              ),
            }));
          }
          if (active) setEvents((previous) => mergeEvent(previous, event));
        });
        const [finalRun, finalArtifacts] = await Promise.all([
          apiJson<{ status: string; report: ResearchReport | null }>(
            `/api/research-runs/${encodeURIComponent(runId)}`,
            { signal: controller.signal },
          ),
          apiJson<ResearchArtifact[]>(
            `/api/research-runs/${encodeURIComponent(runId)}/artifacts`,
            { signal: controller.signal },
          ),
        ]);
        if (active) {
          setRunStatus(finalRun.status);
          setReport(finalRun.report);
          setArtifacts(finalArtifacts);
          setBusy(false);
        }
      } catch (cause) {
        if (active) {
          if (cause instanceof Error && cause.name !== "AbortError")
            setErrors((current) => ({ ...current, run: cause.message }));
        }
      } finally {
        if (active) setRunRetrieving(false);
      }
    };
    void restoreRun();
    return () => {
      active = false;
      controller.abort();
    };
  }, [pathname, runId, section]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadHistory(), 0);
    return () => window.clearTimeout(timer);
  }, [loadHistory]);

  useEffect(() => {
    if (
      !accountId ||
      !stateRestored ||
      restoredFor.current !== accountId ||
      !historyLoaded ||
      errors.history ||
      runId ||
      section === "experiment-studio" ||
      section === "settings"
    )
      return;
    const latest =
      savedRuns.find((run) => ["COMPLETE", "PARTIAL"].includes(run.status)) ??
      savedRuns[0];
    if (latest) setRunId(latest.run_id);
  }, [
    accountId,
    stateRestored,
    historyLoaded,
    errors.history,
    runId,
    savedRuns,
    section,
  ]);

  const contrast = artifacts.find(
    (item) => item.tool_name === "compare_regimes",
  );
  const ranking = artifacts.find((item) => item.tool_name === "rank_genotypes");
  const resultValues = record(contrast?.results);
  const means = record(resultValues.mean_yield_by_regime);
  const topGenotypes = useMemo(
    () =>
      (
        (record(ranking?.results).genotypes as
          Array<Record<string, unknown>> | undefined) ?? []
      ).slice(0, 12),
    [ranking],
  );
  const sectionCopy = SECTION_COPY[section];
  const showOverview = section === "overview";
  const showExperiment =
    section === "experiment-studio" ||
    section === "settings" ||
    section === "next-experiments";
  const showTimeline = section === "live-experiment";
  const showProvenance = section === "data-library";
  const showEvidence =
    section === "research-results" ||
    section === "genotype-explorer" ||
    section === "trait-analytics" ||
    section === "environments";
  const showGroundedClaims = section === "ai-insights";
  const showReproducibility = section === "reports";
  const showContrast =
    section === "research-results" ||
    section === "trait-analytics" ||
    section === "environments";
  const showRanking =
    section === "research-results" || section === "genotype-explorer";

  async function loadRun(id: string): Promise<boolean> {
    setRunRetrieving(true);
    setErrors((current) => {
      const next = { ...current };
      delete next.run;
      delete next.failedRun;
      return next;
    });
    try {
      if (id !== runId) explicitRunLoad.current = id;
      setRunId(id);
      const initial = await apiJson<{
        status: string;
        report: ResearchReport | null;
      }>(`/api/research-runs/${encodeURIComponent(id)}`);
      setRunStatus(initial.status);
      const seen = new Set<number>();
      await consumeRunEvents(id, (event) => {
        if (seen.has(event.sequence)) return;
        seen.add(event.sequence);
        if (["run.failed", "run.timed_out"].includes(event.event_type)) {
          setErrors((current) => ({
            ...current,
            failedRun: text(event.payload.message, "The research run failed."),
          }));
        }
        setEvents((previous) =>
          [
            ...previous.filter((item) => item.sequence !== event.sequence),
            event,
          ].sort((left, right) => left.sequence - right.sequence),
        );
        if (event.event_type === "stage.changed")
          setRunStatus(text(event.payload.stage, initial.status));
      });
      const [finalRun, nextArtifacts] = await Promise.all([
        apiJson<{ status: string; report: ResearchReport | null }>(
          `/api/research-runs/${encodeURIComponent(id)}`,
        ),
        apiJson<ResearchArtifact[]>(
          `/api/research-runs/${encodeURIComponent(id)}/artifacts`,
        ),
      ]);
      setArtifacts(nextArtifacts);
      setReport(finalRun.report);
      setRunStatus(finalRun.status);
      setReplayIndex(0);
      const terminal =
        Boolean(finalRun.report) ||
        ["PARTIAL", "FAILED", "CANCELLED", "TIMED_OUT"].includes(
          finalRun.status,
        );
      setBusy(!terminal);
      if (!terminal) window.setTimeout(() => void loadRun(id), 900);
      return true;
    } catch (cause) {
      setBusy(false);
      setErrors((current) => ({
        ...current,
        run:
          cause instanceof Error ? cause.message : "Unable to load this run.",
      }));
      return false;
    } finally {
      setRunRetrieving(false);
    }
  }

  async function runAnalysis(
    configuration?: ResearchConfiguration,
    plan?: ResearchPlan | null,
  ): Promise<void> {
    setBusy(true);
    setErrors((current) => {
      const next = { ...current };
      delete next.start;
      delete next.failedRun;
      return next;
    });
    setReport(null);
    setArtifacts([]);
    setEvents([]);
    setRunStatus("QUEUED");
    try {
      const accepted = await apiJson<{
        run_id: string;
        status: string;
        report: ResearchReport | null;
      }>("/api/research-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective,
          mode,
          seed: 2026,
          configuration,
          plan,
        }),
      });
      setRunId(accepted.run_id);
      if (accepted.report) {
        await loadRun(accepted.run_id);
      } else {
        setRunStatus(accepted.status);
        setBusy(true);
        void loadRun(accepted.run_id);
      }
      await loadHistory();
    } catch (cause) {
      setBusy(false);
      setRunStatus("FAILED");
      setErrors((current) => ({
        ...current,
        start:
          cause instanceof Error
            ? cause.message
            : "The research request failed.",
      }));
    }
  }

  async function cancelRun(): Promise<void> {
    if (!runId) return;
    setCanceling(true);
    setErrors((current) => {
      const next = { ...current };
      delete next.cancel;
      return next;
    });
    try {
      await apiJson(`/api/research-runs/${encodeURIComponent(runId)}/cancel`, {
        method: "POST",
      });
      setRunStatus("CANCEL_REQUESTED");
      await loadRun(runId);
    } catch (cause) {
      setErrors((current) => ({
        ...current,
        cancel: cause instanceof Error ? cause.message : "Cancellation failed.",
      }));
    } finally {
      setCanceling(false);
    }
  }

  async function replaySavedRun(id: string): Promise<void> {
    setReplayLoadingId(id);
    setEvents([]);
    setArtifacts([]);
    setReport(null);
    setReplayIndex(0);
    setPresenting(false);
    try {
      const loaded = await loadRun(id);
      if (loaded) {
        setReplayIndex(0);
        setPresenting(true);
      }
    } finally {
      setReplayLoadingId("");
    }
  }

  async function retryError(
    context: ErrorContext,
    retry: () => void | Promise<void>,
  ): Promise<void> {
    setRetryingContext(context);
    try {
      await retry();
    } finally {
      setRetryingContext(null);
    }
  }

  const providerLabel =
    report?.mode === "meta" && report.model_id
      ? `Meta · ${report.model_id}`
      : "Deterministic replay · no model call";

  const renderedChoice1 = (() => {
    if (section === "next-experiments") {
      return "Frame the next research question.";
    }
    if (section === "settings") {
      return "Analysis configuration.";
    }
    return "Ask a question. Follow the evidence.";
  })();
  return (
    <div
      className={`app-shell${presenting ? " presentation" : ""}${runRetrieving ? " experiment-retrieving" : ""}${sidebarCollapsed ? " sidebar-is-collapsed" : ""}${mobileNavOpen ? " mobile-nav-open" : ""}`}
    >
      <WorkspaceSidebar
        section={section}
        collapsedNavGroups={collapsedNavGroups}
        toggleNavGroup={toggleNavGroup}
        sidebarRef={sidebarRef}
        isMobileViewport={isMobileViewport}
        mobileNavOpen={mobileNavOpen}
        setMobileNavOpen={setMobileNavOpen}
        mobileNavCloseRef={mobileNavCloseRef}
        mobileNavTriggerRef={mobileNavTriggerRef}
      />
      <div className="main-column">
        <WorkspaceHeader
          title={pageTitle ?? sectionCopy.title}
          providerLabel={providerLabel}
          runId={runId}
          savedRuns={savedRuns}
          onSelectRun={(id) => {
            setEvents([]);
            setArtifacts([]);
            setReport(null);
            setReplayIndex(0);
            setRunId(id);
          }}
          account={
            account && accountDisplayName
              ? { ...account, display_name: accountDisplayName }
              : account
          }
          isOverview={showOverview}
          sidebarCollapsed={sidebarCollapsed}
          setSidebarCollapsed={setSidebarCollapsed}
          mobileNavOpen={mobileNavOpen}
          setMobileNavOpen={setMobileNavOpen}
          mobileNavTriggerRef={mobileNavTriggerRef}
        />

        <main
          key={section}
          id="main"
          className={`page-content${showOverview ? " overview-page" : " detail-page"}`}
        >
          {children ?? (
            <>
              {Object.entries(errors).map(([context, details]) => {
                const errorCopy: Record<
                  ErrorContext,
                  {
                    title: string;
                    description: string;
                    action: string;
                    retry: () => void | Promise<void>;
                  }
                > = {
                  dataset: {
                    title: "Dataset profile unavailable",
                    description:
                      "The verified source summary could not be loaded. You can retry without losing your current workspace.",
                    action: "Reload dataset",
                    retry: loadProfile,
                  },
                  history: {
                    title: "Saved runs couldn’t be loaded",
                    description:
                      "Your current workspace is still available. Try loading saved runs again.",
                    action: "Reload saved runs",
                    retry: loadHistory,
                  },
                  run: {
                    title: "This run couldn’t be opened",
                    description:
                      "The saved run may be temporarily unavailable. Try loading its persisted events and results again.",
                    action: "Reload run",
                    retry: async () => {
                      if (runId) await loadRun(runId);
                    },
                  },
                  start: {
                    title: "The research run couldn’t start",
                    description:
                      "Check the research question and analysis configuration, then try starting a new run.",
                    action: "Try again",
                    retry: runAnalysis,
                  },
                  cancel: {
                    title: "Cancellation wasn’t confirmed",
                    description:
                      "The run may still be active. Retry the cancellation request or check its saved timeline.",
                    action: "Retry cancellation",
                    retry: cancelRun,
                  },
                  failedRun: {
                    title: "The research run stopped before completing",
                    description:
                      "No completed report is available for this run. You can start a fresh attempt; previous saved events remain available.",
                    action: "Start a new run",
                    retry: runAnalysis,
                  },
                };
                const errorContext = context as ErrorContext;
                const copy = errorCopy[errorContext];
                return (
                  <WorkspaceErrorItem
                    key={context}
                    context={errorContext}
                    details={details}
                    copy={copy}
                    retrying={retryingContext === errorContext}
                    onRetry={retryError}
                  />
                );
              })}

              {!showOverview && (
                <section className="page-title-block">
                  <span className="eyebrow">NEUROLAB RESEARCH WORKSPACE</span>
                  <h1>{sectionCopy.title}</h1>
                  <p>{sectionCopy.description}</p>
                </section>
              )}

              {showOverview && (
                <WorkspaceOverview
                  profile={profile}
                  profileLoading={profileLoading}
                  runStatus={runStatus}
                  busy={busy}
                  reducedMotion={reducedMotion}
                />
              )}

              {showExperiment && (
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">RESEARCH WORKSPACE</span>
                    <h2>{renderedChoice1}</h2>
                  </div>
                  <span className="workspace-caption">
                    REAL DATA · PERSISTED RUNS · TRACEABLE RESULTS
                  </span>
                </div>
              )}

              {showTimeline && (
                <CinematicPlayer
                  runId={runId}
                  runStatus={runStatus}
                  report={report}
                  events={events}
                  artifacts={artifacts}
                  reducedMotion={reducedMotion}
                  retrieving={runRetrieving}
                  playing={presenting}
                  setPlaying={setPresenting}
                  index={replayIndex}
                  setIndex={setReplayIndex}
                  downloadFile={downloadFile}
                />
              )}

              <section
                className={`workspace-grid workspace-${section}`}
                aria-label={sectionCopy.title}
              >
                {showExperiment && (
                  <ExperimentSetup
                    objective={objective}
                    setObjective={setObjective}
                    mode={mode}
                    setMode={setMode}
                    busy={busy}
                    canceling={canceling}
                    runId={runId}
                    runStatus={runStatus}
                    toolCalls={report?.tool_calls}
                    runAnalysis={runAnalysis}
                    cancelRun={cancelRun}
                  />
                )}

                {showProvenance && (
                  <SourceProvenance
                    profile={profile}
                    profileLoading={profileLoading}
                    report={report}
                  />
                )}

                {showEvidence && (
                  <EvidenceResults
                    section={section}
                    artifacts={artifacts}
                    report={report}
                    events={events}
                    retrieving={runRetrieving}
                    showContrast={showContrast}
                    showRanking={showRanking}
                    contrast={contrast}
                    ranking={ranking}
                    resultValues={resultValues}
                    means={means}
                    topGenotypes={topGenotypes}
                    contrastCI={
                      record(contrast?.uncertainty).yield_difference_95_ci_kg_ha
                    }
                    formatNumber={number}
                    downloadFile={downloadFile}
                  />
                )}

                {showTimeline && (
                  <ResearchTimeline
                    events={events}
                    runRetrieving={runRetrieving}
                    runId={runId}
                    runStatus={runStatus}
                    presenting={presenting}
                    setPresenting={setPresenting}
                    replayIndex={replayIndex}
                    setReplayIndex={setReplayIndex}
                    replayLoadingId={replayLoadingId}
                    historyLoading={historyLoading}
                    historyLoaded={historyLoaded}
                    historyError={errors.history}
                    savedRuns={savedRuns}
                    loadHistory={loadHistory}
                    replaySavedRun={replaySavedRun}
                  />
                )}
              </section>

              {report && isScientificReportSection(section) && (
                <ScientificReportView
                  report={report}
                  downloadFile={downloadFile}
                />
              )}
              {report &&
                (showReproducibility || showTimeline || showExperiment) && (
                  <ResearchRunPlan report={report} />
                )}

              {showReproducibility && (
                <section
                  className="report-strip"
                  id="report-strip"
                  aria-label="Reproducibility report"
                >
                  {report ? (
                    <>
                      <div>
                        <span>RUN</span>
                        <code>{report.run_id}</code>
                      </div>
                      <div>
                        <span>SEED</span>
                        <code>{report.seed}</code>
                      </div>
                      <div>
                        <span>ANALYSIS</span>
                        <code>
                          {report.mode === "meta"
                            ? `${report.model_provider ?? "Meta"} · ${report.model_id ?? "configured model"}`
                            : "Deterministic replay · no inference"}
                        </code>
                      </div>
                      <div>
                        <span>CLAIM SCOPE</span>
                        <code>Observational / exploratory</code>
                      </div>
                      {report.limitations.map((limitation) => (
                        <p className="report-limitation" key={limitation}>
                          {limitation}
                        </p>
                      ))}
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
                              [
                                "artifact_id,tool_name,claim_scope,sample_size,source_sha256",
                                ...artifacts.map(
                                  (item) =>
                                    `${item.artifact_id},${item.tool_name},${item.claim_scope},${item.sample_size},${item.source_sha256}`,
                                ),
                              ].join("\n"),
                              "text/csv",
                            )
                          }
                        >
                          Export artifact index CSV
                        </button>
                      </div>
                    </>
                  ) : (
                    <EmptyState
                      icon="report"
                      title="No completed report selected"
                      description="Run or replay an experiment to see its seed, source identity, analysis mode, limitations, and artifact exports."
                      action={
                        <Link
                          className="primary-link"
                          href="/experiment-studio"
                        >
                          Create a research run{" "}
                          <span aria-hidden="true">↗</span>
                        </Link>
                      }
                    />
                  )}
                </section>
              )}
              {showGroundedClaims && (
                <section
                  className="grounded-report"
                  id="grounded-report"
                  aria-label="Evidence-linked report claims"
                >
                  <div className="card-head">
                    <span className="eyebrow">EVIDENCE-LINKED INSIGHTS</span>
                  </div>
                  <h2>Research insights</h2>
                  {report?.grounded_claims &&
                  report.grounded_claims.length > 0 ? (
                    report.grounded_claims.map((item) => (
                      <p
                        className="grounded-claim"
                        key={item.evidence_ids.join("-")}
                      >
                        <span>
                          {item.claim_scope} · evidence{" "}
                          {item.evidence_ids.join(", ")}
                        </span>
                        {item.claim}
                      </p>
                    ))
                  ) : (
                    <EmptyState
                      compact
                      icon="insight"
                      title="No evidence-linked insights yet"
                      description="AI narratives are not scientific results. Complete a run with persisted tool evidence to review grounded claims."
                      action={
                        <Link
                          className="primary-link"
                          href="/experiment-studio"
                        >
                          Start an experiment <span aria-hidden="true">↗</span>
                        </Link>
                      }
                    />
                  )}
                </section>
              )}
            </>
          )}
        </main>

        <footer className="footer">
          <span>NEUROLAB AI © 2026 · EVIDENCE WORKSPACE</span>
          <span>
            Observational results are not causal findings · No crop measurements
            are simulated
          </span>
        </footer>
      </div>
    </div>
  );
}
