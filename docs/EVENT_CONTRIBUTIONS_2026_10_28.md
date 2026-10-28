# Conservative event-contribution disclosure

The supplied guide requires judges to clearly identify new work. This document identifies reviewable source changes; it does not certify organizer eligibility or prove creation time from commit timestamps.

## Baseline and ambiguity

Use source snapshot `8fde534` as the conservative disclosure baseline. Its first source import contains earlier Oct 26/27 implementation logs and no earlier source Git history. Some work may have been written after kickoff, but the guide separately states an Oct 27 building-period start. Do not claim that every file first committed on Oct 27 was authored on that date. Do not call this whole snapshot pre-event with certainty either. Until clarified, disclose it as the earlier prototype/baseline and highlight demonstrable subsequent changes.

The [machine-readable inventory](../verification/event-readiness-2026-10-28/contribution-inventory.json) compares that baseline with `aaacaf2`. It lists 101 subsequent commits and 122 changed source/test/config files with exact blob hashes. Added lines and file creation are not effort, novelty, impact or eligibility scores. Refactors can reuse existing code.

## Reviewable subsequent contributions

| Contribution to highlight | Source/history evidence | Claim boundary |
|---|---|---|
| Account-scoped long-form objective input and persistence | `1fac9f9`; current [ExperimentSetup](../app/workspace/ExperimentSetup.tsx) and [research context](../neurolab/research_context.py) | Highlight the specific input/persistence changes, not invention of authentication or the whole app |
| Measured-results redesign, iconography and numeric views | `a202e79`; current [EvidenceResults](../app/workspace/EvidenceResults.tsx) | Charts visualize recorded tool results; data and measurements are not newly collected by us |
| Truthful cinematic replay and redesigned setup/provenance | `0ef2945`; current [CinematicPlayer](../app/workspace/CinematicPlayer.tsx) | Replay of stored events, not live crop simulation or hidden model reasoning |
| Added trait-association and observed-environment sensitivity methods | `9666c16`; [descriptive methods](../neurolab/descriptive.py) | Descriptive/conditional uncertainty; no validated field tolerance, causal irrigation or independent source replication |
| Structured Ghana hypothesis assessments and reports | `62ff746`; [scientific report](../neurolab/scientific_report.py) | Retrospective criteria and evidence-linked claims; no confirmatory preregistration |
| Portable report and saved-data figure exports | `5caffa6`; [exporter](../scripts/export_investigation.py) | Presentation of actual saved values, not a new scientific run |
| Durable owned jobs, shared reservations and failure handling | Post-baseline commits in inventory; [jobs](../neurolab/jobs.py), [model spending](../neurolab/model_spend.py) | Distinguish actual hosted receipts from fixture tests and production-only operational gaps |
| Real Meta investigation and recorded five-policy comparison | [original objective analysis](../verification/ORIGINAL_OBJECTIVE_FAILURE_ANALYSIS.md), [actual comparison](LIVE_COMPARISON_2026_10_28.md) | 180 records/144 requests are collected; human ratings remain unfilled and there is no policy winner |
| Baseten function-call adapter and isolated vendor configuration | `97fce76`, [provider](../neurolab/providers.py), [configuration](../neurolab/model_configuration.py) | Generic hosted run is real; the event's `-1026` alias returned404 and is not verified. Do not claim partner-approved bonus eligibility |

Inspect the actual diffs before showing snippets. The current source includes later fixes; a linked current file is not a statement that all of it was created in its cited commit.

## Reused context to disclose

- Existing Ghana/IITA datasets, source dictionaries, licenses and measured values; cite the original authors.
- Earlier prototype, original four-tool functionality/authentication and pre-inventory material whose exact creation window is not established.
- Supplied NeuroLab branding, fonts, React/Next/FastAPI/scientific/visualization libraries and Meta model weights/services.
- Original planning/specification documents: they are requirements, not code newly built in the event.
- Generated narration: synthetic local speech, not a human recording or new model research contribution.

## Video disclosure wording

“I started from an earlier NeuroLab prototype and existing published maize data. During this event I added the long-form objective workflow, trait and environment analyses, evidence-linked reports and exports, durable execution safeguards, and the recorded model comparison. I’ll demonstrate those additions; the dataset, prior prototype and third-party assets are reused context.”

Use only the clauses supported by the final selected feature diffs and actual demo. Do not say “built everything from scratch” or claim an unresolved `-1026` run. Show a short actual source-diff/commit view so the new code is identifiable. Keep baseline screens as necessary context rather than presenting them as new deliverables. Organizer clarification is still needed for any earlier work the entrant wishes to claim.
