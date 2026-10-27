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
  scientific_report?: ScientificReport | null;
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

export type ScientificHypothesis = {
  id: string;
  proposal: string;
  rationale: string;
  criterion: string;
  verdict: string;
  findings: string;
  evidence_ids: string[];
  contradictions: string[];
  scope: string;
  matching_genotype_ids?: string[];
};
export type InvestigationCandidate = {
  genotype_id: string;
  drought_mean_kg_ha: number;
  environment_mean_sd_kg_ha: number | null;
  environment_centered_sd_kg_ha: number | null;
  environment_count: number;
  omitted_environment_rank_range: number[] | null;
  evidence_ids: string[];
  selection_basis: string;
  meets_observed_top_quartile_each_environment?: boolean | null;
  observed_regime_summary: {
    well_watered_mean_kg_ha: number;
    descriptive_retention_percent: number | null;
    drought_plot_count: number;
    well_watered_plot_count: number;
  } | null;
};
export type ScientificReport = {
  version: string;
  scope: string;
  objective?: string;
  evidence_coverage: string;
  conclusion_status?: string;
  additional_hypotheses_not_assessed?: string[];
  inventory_manifest_sha256?: string | null;
  missing_tools?: string[];
  hypothesis_evaluations: ScientificHypothesis[];
  source_citations?: {
    authors: string;
    doi: string;
    license: string;
    role: string;
  }[];
  dataset_inventory_evidence_ids?: string[];
  dataset_inventory?: {
    source_file: string;
    source_sha256: string;
    physical_rows: number;
    substantive_rows: number;
    fully_empty_rows: number;
    analysis_enabled: boolean;
    eligibility_reason: string;
    original_columns: string[];
    count_provenance: string;
  }[];
  candidate_summaries?: InvestigationCandidate[];
  methodology?: {
    dependent_variable: string;
    explanatory_variables: string;
    design: string;
    methods: {
      tool: string;
      analysis_version: string;
      sample_size: number;
      uncertainty: unknown;
      evidence_id: string;
    }[];
    assumptions_and_limits: string[];
  };
  findings?: {
    observed_regime_comparison: {
      results: {
        mean_yield_by_regime: Record<string, number>;
        yield_difference_kg_ha: number;
        drought_to_well_watered_yield_ratio_percent: number | null;
        plot_count_by_regime: Record<string, number>;
      };
      uncertainty: { yield_difference_95_ci_kg_ha: number[] };
      evidence_ids: string[];
    } | null;
    trait_associations: {
      associations: {
        trait: string;
        unit: string;
        genotype_count: number;
        spearman_rho: number | null;
        spearman_rho_95_percentile_interval: number[] | null;
      }[];
      screen_summary: string;
      evidence_ids: string[];
    } | null;
  };
  follow_up_analysis?: {
    analysis: string;
    executed: boolean;
    adaptively_selected: boolean;
    selection_source: string;
    uncertainty_addressed: string;
    remaining_uncertainty: string;
    selection_evidence_ids: string[];
    result_evidence_ids: string[];
  };
  next_experiment?: {
    status: string;
    title: string;
    candidate_ids: string[];
    basis_evidence_ids: string[];
    design: string;
    additional_data: string[];
    analysis_plan: string;
    sample_size: string;
    reference: { title: string; url: string };
  };
  reproducibility?: {
    code_commit: string | null;
    python_version: string;
    snapshot: string;
    module_sha256: Record<string, string>;
    dirty_status_note: string;
  };
  unresolved_scope?: string[];
};
