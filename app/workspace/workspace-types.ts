import type {
  ResearchConfiguration,
  ResearchPlan,
} from "./research-editor-types";

export type WorkspaceSection =
  | "overview"
  | "experiment-studio"
  | "live-experiment"
  | "research-results"
  | "genotype-explorer"
  | "trait-analytics"
  | "environments"
  | "data-library"
  | "ai-insights"
  | "next-experiments"
  | "reports"
  | "settings";

export type DatasetProfile = {
  row_count: number;
  genotype_count: number;
  source_sha256: string;
  year_codes?: string[];
  water_regimes?: Record<string, number>;
};

export type ResearchReport = {
  run_id: string;
  dataset_id: string;
  source_sha256: string;
  mode: string;
  replay_label: string;
  model_provider?: string | null;
  model_id?: string | null;
  objective: string;
  refined_objective?: string;
  research_plan?: ResearchPlan;
  research_configuration?: ResearchConfiguration;
  seed: number;
  tool_calls: number;
  completion_status: string;
  limitations: string[];
  evidence_ids: string[];
  grounded_claims?: Array<{
    claim: string;
    evidence_ids: string[];
    claim_scope: string;
  }>;
};

export type ResearchEvent = {
  event_id: string;
  run_id: string;
  sequence: number;
  timestamp: string;
  event_type: string;
  payload: Record<string, unknown>;
};

export type ResearchArtifact = {
  artifact_id: string;
  source_sha256: string;
  source_file: string;
  analysis_version: string;
  tool_name: string;
  claim_scope: string;
  sample_size: number;
  results: Record<string, unknown>;
  uncertainty: Record<string, unknown> | null;
  warnings: string[];
};

export type SavedRun = {
  run_id: string;
  objective: string;
  status: string;
  created_at: string;
  source_sha256: string;
};

export type ErrorContext =
  "dataset" | "history" | "run" | "start" | "cancel" | "failedRun";
export type WorkspaceErrors = Partial<Record<ErrorContext, string>>;

export type NavigationGroup = {
  id: string;
  label: string;
  icon: string;
  items: Array<{ section: WorkspaceSection; label: string; icon: string }>;
};
