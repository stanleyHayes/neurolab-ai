"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { authenticatedFetch } from "../auth-client";
import {
  configurationError,
  defaultConfiguration,
  objectiveError,
} from "./research-editor-types";
import type {
  DraftResponse,
  ResearchConfiguration,
  ResearchDraft,
  ResearchPlan,
} from "./research-editor-types";

export async function editorRequest<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await authenticatedFetch(url, init);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    let detail = `Request failed (HTTP ${response.status}). Your objective and configuration were kept.`;
    if (typeof payload.detail === "string") detail = payload.detail;
    else if (
      Array.isArray(payload.detail) &&
      typeof payload.detail[0]?.msg === "string"
    )
      detail = payload.detail[0].msg;
    throw new Error(detail);
  }
  return payload as T;
}
const jsonRequest = (value: unknown, method = "POST"): RequestInit => ({
  method,
  headers: { "content-type": "application/json" },
  body: JSON.stringify(value),
});

export function useResearchEditor(
  objective: string,
  setObjective: Dispatch<SetStateAction<string>>,
) {
  const [configuration, setConfiguration] = useState(defaultConfiguration);
  const [acceptedPlan, setAcceptedPlan] = useState<ResearchPlan | null>(null);
  const [proposal, setProposal] = useState<ResearchPlan | null>(null);
  const [proposalOriginal, setProposalOriginal] = useState("");
  const [proposalStale, setProposalStale] = useState(false);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dirty, setDirty] = useState(false);
  const edited = useRef(false);
  const changes = useRef(0);
  const proposalRevision = useRef(0);
  const mounted = useRef(true);

  const applyDraft = useCallback(
    (stored: DraftResponse) => {
      const {
        objective: original,
        accepted_plan: plan,
        ...config
      } = stored.draft;
      setObjective(original);
      setConfiguration(config);
      setAcceptedPlan(plan);
      setProposal(null);
      setRevision(stored.revision);
      setDirty(false);
      edited.current = false;
      setNotice(
        "Saved draft restored from your account. Original formatting is preserved.",
      );
    },
    [setObjective],
  );
  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    void editorRequest<DraftResponse>("/api/research-draft", {
      signal: controller.signal,
    })
      .then((stored) => {
        if (!mounted.current) return;
        setRevision(stored.revision);
        if (stored.revision > 0 && !edited.current) applyDraft(stored);
        if (stored.revision > 0 && edited.current)
          setNotice(
            "A saved draft is available. Your current writing was kept; use Load saved draft to replace it.",
          );
      })
      .catch((cause) => {
        if (mounted.current && cause.name !== "AbortError")
          setError(
            "Could not load your saved draft. Your current writing is kept. " +
              cause.message,
          );
      })
      .finally(() => {
        if (mounted.current) setLoading(false);
      });
    return () => {
      mounted.current = false;
      controller.abort();
    };
  }, [applyDraft]);

  const changed = () => {
    changes.current += 1;
    setProposalStale(true);
    edited.current = true;
    setDirty(true);
    setNotice("");
    setError("");
  };
  const changeObjective = (value: string) => {
    changed();
    setObjective(value);
    setAcceptedPlan(null);
  };
  const changeConfiguration = (value: ResearchConfiguration) => {
    changed();
    setConfiguration(value);
    setAcceptedPlan(null);
  };
  const validation =
    objectiveError(objective) || configurationError(configuration);
  const draft: ResearchDraft = {
    ...configuration,
    objective,
    accepted_plan: acceptedPlan,
  };

  async function saveDraft() {
    if (validation) {
      setError(validation);
      return;
    }
    const savingRevision = changes.current;
    setSaving(true);
    setError("");
    try {
      const saved = await editorRequest<DraftResponse>(
        "/api/research-draft",
        jsonRequest({ expected_revision: revision, draft }, "PUT"),
      );
      if (!mounted.current) return;
      setRevision(saved.revision);
      setDirty(changes.current !== savingRevision);
      setNotice(
        changes.current === savingRevision
          ? "Draft saved to your account. You can resume after a refresh."
          : "Earlier draft saved. Your newer writing is kept and still has unsaved changes.",
      );
    } catch (cause) {
      if (mounted.current)
        setError(
          cause instanceof Error
            ? cause.message
            : "Draft save failed. Your writing is kept.",
        );
    } finally {
      if (mounted.current) setSaving(false);
    }
  }
  async function loadDraft() {
    setLoading(true);
    setError("");
    try {
      const stored = await editorRequest<DraftResponse>("/api/research-draft");
      if (!mounted.current) return;
      if (stored.revision > 0) applyDraft(stored);
      else
        setNotice(
          "There is no saved draft in this account yet. Your writing is kept.",
        );
    } catch (cause) {
      if (mounted.current)
        setError(
          cause instanceof Error ? cause.message : "Draft retrieval failed.",
        );
    } finally {
      if (mounted.current) setLoading(false);
    }
  }
  async function refine() {
    if (validation) {
      setError(validation);
      return;
    }
    const original = objective;
    const refiningRevision = changes.current;
    setRefining(true);
    setError("");
    setNotice("");
    try {
      const result = await editorRequest<{
        original_objective: string;
        plan: ResearchPlan;
      }>(
        "/api/research-objectives/refine",
        jsonRequest({ objective: original, configuration }),
      );
      if (result.original_objective !== original)
        throw new Error(
          "Refinement did not preserve the submitted objective; proposal was rejected.",
        );
      if (mounted.current) {
        proposalRevision.current = refiningRevision;
        setProposalStale(changes.current !== refiningRevision);
        setProposalOriginal(original);
        setProposal(result.plan);
        setNotice(
          "Meta proposal received. Review it beside your unchanged original; it has not been accepted.",
        );
      }
    } catch (cause) {
      if (mounted.current)
        setError(
          cause instanceof Error
            ? cause.message
            : "Refinement unavailable. Your original objective is kept.",
        );
    } finally {
      if (mounted.current) setRefining(false);
    }
  }
  function acceptProposal() {
    if (
      !proposal ||
      proposalOriginal !== objective ||
      changes.current !== proposalRevision.current
    ) {
      setError(
        "The original objective or configuration changed. Refine it again before accepting this proposal.",
      );
      return;
    }
    const proposalError = objectiveError(proposal.refined_objective);
    if (proposalError) {
      setError("Refined proposal: " + proposalError);
      return;
    }
    changed();
    setAcceptedPlan(proposal);
    setConfiguration({
      ...configuration,
      title: proposal.title,
      research_questions: proposal.research_questions,
      hypotheses: proposal.hypotheses,
      desired_outputs: proposal.desired_outputs,
    });
    setProposal(null);
    setNotice(
      "Research plan accepted. The original objective was not changed. Save the draft to retain this plan.",
    );
  }
  function rejectProposal() {
    setProposal(null);
    setNotice(
      "Proposal rejected. Your original objective and configuration were kept.",
    );
  }
  return {
    configuration,
    acceptedPlan,
    proposal,
    setProposal,
    proposalOriginal,
    proposalStale: proposalStale || proposalOriginal !== objective,
    revision,
    loading,
    saving,
    refining,
    error,
    notice,
    dirty,
    validation,
    changeObjective,
    changeConfiguration,
    saveDraft,
    loadDraft,
    refine,
    acceptProposal,
    rejectProposal,
  };
}
export type ResearchEditorState = ReturnType<typeof useResearchEditor>;
