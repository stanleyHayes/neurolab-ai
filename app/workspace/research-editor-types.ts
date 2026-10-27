export const OBJECTIVE_LIMIT = 20_000;
export const METHODS = [
  {
    id: "trait_associations",
    label: "Trait associations",
    detail:
      "Genotype-mean drought associations with conditional bootstrap intervals",
  },
  {
    id: "environment_stability",
    label: "Environment sensitivity",
    detail:
      "Observed yield variation and leave-one-environment-out ranks; not validated stability",
  },
  {
    id: "block_bootstrap_contrast",
    label: "Regime contrast",
    detail: "Environment-stratified yields and block-bootstrap uncertainty",
  },
  {
    id: "genotype_ranking",
    label: "Genotype summaries",
    detail: "Descriptive drought yields; not a validated stability ranking",
  },
  {
    id: "missingness_audit",
    label: "Missingness audit",
    detail: "Missing observations and structural gaps",
  },
  {
    id: "dataset_profile",
    label: "Dataset profile",
    detail: "Source lineage, design and record counts",
  },
] as const;
export const OUTPUTS = [
  "research_report",
  "regime_contrast",
  "genotype_summaries",
  "missingness_summary",
  "provenance_export",
  "trait_associations",
  "environment_summaries",
] as const;
export type ResearchMethod = (typeof METHODS)[number]["id"];
export type ResearchOutput = (typeof OUTPUTS)[number];
export type DatasetId =
  | "ghana_combined"
  | "iita_drought"
  | "iita_full_irrigation"
  | "iita_multiloc"
  | "iita_striga";
export type ResearchConfiguration = {
  title: string;
  research_questions: string[];
  hypotheses: string[];
  dataset_id: DatasetId;
  constraints: {
    max_steps: number;
    max_tool_calls: number;
    max_seconds: number;
  };
  preferred_methods: ResearchMethod[];
  desired_outputs: ResearchOutput[];
  autonomy_preferences: {
    auto_plan_with_meta: boolean;
    execute_supported_tasks: boolean;
    stop_if_unsupported: boolean;
  };
};
export type ResearchPlan = {
  objective_sha256: string;
  planning_mode: "deterministic" | "meta";
  title: string;
  important_constraints?: string[];
  refined_objective: string;
  ambiguities: string[];
  research_questions: string[];
  hypotheses: string[];
  dataset_suggestions: {
    dataset_id: DatasetId;
    rationale: string;
    enabled_for_analysis: boolean;
  }[];
  analysis_approaches: { method_id: ResearchMethod; rationale: string }[];
  desired_outputs: ResearchOutput[];
  tasks: {
    task_id: string;
    title: string;
    description: string;
    tool_name: string | null;
    status: "pending" | "completed" | "unsupported";
    evidence_ids: string[];
  }[];
  unsupported_requirements: string[];
};
export type ResearchDraft = ResearchConfiguration & {
  objective: string;
  accepted_plan: ResearchPlan | null;
};
export type DraftResponse = {
  revision: number;
  draft: ResearchDraft;
  updated_at: string | null;
};
export function defaultConfiguration(): ResearchConfiguration {
  return {
    title: "",
    research_questions: [],
    hypotheses: [],
    dataset_id: "ghana_combined",
    constraints: { max_steps: 3, max_tool_calls: 5, max_seconds: 60 },
    preferred_methods: [],
    desired_outputs: [],
    autonomy_preferences: {
      auto_plan_with_meta: true,
      execute_supported_tasks: true,
      stop_if_unsupported: false,
    },
  };
}
export function textLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}
export function objectiveError(value: string): string {
  if (!value.trim())
    return "Enter a research objective before starting an investigation.";
  if (Array.from(value).length > OBJECTIVE_LIMIT)
    return "The objective exceeds 20,000 characters. Your full text is kept; shorten it before saving or running.";
  return "";
}
export function configurationError(config: ResearchConfiguration): string {
  const {
    max_steps: steps,
    max_tool_calls: calls,
    max_seconds: seconds,
  } = config.constraints;
  if (!Number.isInteger(steps) || steps < 1 || steps > 6)
    return "Analysis steps must be an integer from 1 to 6.";
  if (!Number.isInteger(calls) || calls < 1 || calls > 10)
    return "Tool calls must be an integer from 1 to 10.";
  if (!Number.isInteger(seconds) || seconds < 1 || seconds > 180)
    return "Time budget must be an integer from 1 to 180 seconds.";
  if (config.research_questions.length > 20 || config.hypotheses.length > 20)
    return "Use at most 20 research questions and 20 hypotheses.";
  return "";
}
