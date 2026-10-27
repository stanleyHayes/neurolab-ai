import type { NavigationGroup, WorkspaceSection } from "./workspace-types";

export const WORKSPACE_SECTIONS: WorkspaceSection[] = [
  "overview",
  "experiment-studio",
  "live-experiment",
  "research-results",
  "genotype-explorer",
  "trait-analytics",
  "environments",
  "data-library",
  "ai-insights",
  "next-experiments",
  "reports",
  "settings",
];

export const WORKSPACE_NAV_GROUPS: NavigationGroup[] = [
  {
    id: "workspace",
    label: "Workspace",
    icon: "◈",
    items: [{ section: "overview", label: "Overview", icon: "◈" }],
  },
  {
    id: "experiments",
    label: "Experiments",
    icon: "⚗",
    items: [
      { section: "experiment-studio", label: "Experiment Studio", icon: "⚗" },
      { section: "live-experiment", label: "Live Experiment", icon: "◉" },
    ],
  },
  {
    id: "evidence",
    label: "Evidence",
    icon: "▥",
    items: [
      { section: "research-results", label: "Research Results", icon: "▥" },
      { section: "genotype-explorer", label: "Genotype Explorer", icon: "❀" },
      { section: "trait-analytics", label: "Trait Analytics", icon: "⌁" },
      { section: "environments", label: "Environments", icon: "◎" },
      { section: "data-library", label: "Data Library", icon: "▤" },
    ],
  },
  {
    id: "research",
    label: "Research planning",
    icon: "✧",
    items: [
      { section: "ai-insights", label: "AI Insights", icon: "✧" },
      { section: "next-experiments", label: "Next Experiments", icon: "↗" },
    ],
  },
  {
    id: "reports",
    label: "Reports & settings",
    icon: "▧",
    items: [
      { section: "reports", label: "Reports", icon: "▧" },
      { section: "settings", label: "Settings", icon: "⚙" },
    ],
  },
];

export const SECTION_COPY: Record<
  WorkspaceSection,
  { title: string; description: string }
> = {
  overview: {
    title: "Overview",
    description: "Evidence-led research on real maize field trials.",
  },
  "experiment-studio": {
    title: "Experiment Studio",
    description:
      "Frame a research question and run a bounded, reproducible analysis.",
  },
  "live-experiment": {
    title: "Live Experiment",
    description: "Follow persisted run events and reopen saved research runs.",
  },
  "research-results": {
    title: "Research Results",
    description: "Review verified outputs from persisted analysis artifacts.",
  },
  "genotype-explorer": {
    title: "Genotype Explorer",
    description:
      "Compare descriptive genotype summaries computed from the observed trial data.",
  },
  "trait-analytics": {
    title: "Trait Analytics",
    description:
      "Inspect observed grain-yield summaries with uncertainty and limitations.",
  },
  environments: {
    title: "Environments",
    description:
      "Review the observed trial-environment comparison and its confounding caveats.",
  },
  "data-library": {
    title: "Data Library",
    description:
      "Inspect source identity, row counts, licensing, and data limitations.",
  },
  "ai-insights": {
    title: "AI Insights",
    description:
      "Read only claims linked to persisted evidence produced by verified tools.",
  },
  "next-experiments": {
    title: "Next Experiments",
    description:
      "Plan a follow-up question without treating suggestions as observed findings.",
  },
  reports: {
    title: "Reports",
    description:
      "Review run reproducibility details and export the persisted evidence.",
  },
  settings: {
    title: "Settings",
    description: "Choose the analysis execution mode for new research runs.",
  },
};

export const INITIAL_OBJECTIVE =
  "Which genotypes warrant follow-up under managed drought, and what limitations affect that comparison?";

export const EVENT_LABELS: Record<string, string> = {
  "report.generated": "Evidence-linked report saved",
  "research.investigation_prepared":
    "Exploratory investigation criteria declared",
  "run.created": "Run created",
  "stage.changed": "Research stage",
  "hypothesis.proposed": "Hypothesis proposed",
  "tool.requested": "Research tool requested",
  "tool.validated": "Tool request validated",
  "tool.completed": "Computation completed",
  "evidence.updated": "Evidence recorded",
  "decision.recorded": "Next analysis selected",
  "decision.failed": "Model decision unavailable",
  "tool.failed": "Analysis recovery",
  "run.cancel_requested": "Cancellation requested",
  "run.cancelled": "Run cancelled",
  "run.failed": "Run failed",
  "run.completed": "Run complete",
  "run.partial": "Partial report — analysis incomplete",
  "research.workflow_proposed": "Research workflow prepared",
};
