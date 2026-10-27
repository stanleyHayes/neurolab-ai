# Research objective editor

The original restriction was the 2,000-character HTML textarea limit in `ExperimentSetup.tsx`, combined with an incomplete migration between legacy top-level run budgets and structured request configuration. The Python source at audit entry also had syntax/import errors. These failures prevented a reliable end-to-end acceptance claim even though some backend draft/refinement foundations already existed.

## User flow

Experiment Studio presents one multiline objective editor. A character counter uses Unicode code points, matching Python's string-length validation, with a 20,000-character supported limit. Text above the limit remains in the editor with an explicit error; saving/refinement/execution is blocked rather than silently deleting text. Paragraphs and Markdown are submitted as the exact textarea string. Markdown/HTML is stored verbatim and displayed through React-escaped text, not executed or injected as HTML.

“Expand writing space” opens a branded native dialog with the same original objective, keyboard dismissal and focus restoration. Optional configuration remains in a collapsed disclosure: title, questions, proposed hypotheses, enabled dataset, methods, desired outputs, research budgets and autonomy preferences. Only the objective is required for an ordinary run. IITA sources are reference-only while their normalization/analysis contracts remain incomplete; the UI never treats them as directly comparable observations.

## Drafts

Save/load uses authenticated `GET`/`PUT /research-draft`. The server derives owner identity from the active JWT and stores JSON with a monotonically increasing revision. A conditional SQL update rejects stale writes with HTTP 409. It never accepts an owner ID from the body. The editor preserves unsaved writing on load/save errors, avoids overwriting typing during its initial load, and keeps newer edits marked unsaved when an earlier in-flight save finishes.

A saved draft is restored after page refresh or re-entry. Draft text is not stored in browser local/session storage. The remembered selected-run locator is keyed by authenticated account ID; old shared objective state is removed. Navigation preferences contain no research text.

## Meta refinement

“Refine Research Objective” is optional and contacts the configured verified server-side adapter. A structured proposal appears beside the unchanged original, including questions, hypotheses, tasks, ambiguities, dataset suggestions and unsupported requirements. Researchers may edit the proposed refinement/questions/hypotheses, accept the plan, or reject it. Acceptance changes the execution plan/configuration, never the original objective. A changed original/configuration invalidates acceptance of an older proposal. Saving the draft retains an accepted plan.

No credentials are returned to the browser. If Meta is unavailable or the response is invalid, the original remains intact and an error is shown. Refinement is a proposal, not a scientific result. Ordinary execution stages do not request repeated approval.

## Execution and inspection

Run requests carry the exact objective plus optional structured configuration and accepted plan. The API rejects conflicting legacy/structured budgets and stale objective hashes. It stores the objective, configuration and plan with the owner-scoped run. Reports expose the original, refined text, task completion and evidence IDs. Plan-only and stop-on-unsupported preferences do not fabricate numeric outputs.

See `RESEARCH_CONTEXT_MANAGEMENT.md` and `../verification/RESEARCH_INPUT_ACCEPTANCE.md` for limits and actual acceptance evidence.
