# Document 09 — Cinematic Scientific Visualization & Interaction Design System
**NeuroLab AI | Meta Global AI Developer Hackathon | 26 October 2026**
**Status:** Implementation specification · **Priority:** P0 research truth, P1 cinematic enhancement

> **Design principle:** Make the experiment feel extraordinary without misrepresenting what the science or AI has actually done.

## 01. Purpose and non-negotiables

Create a cinematic but scientifically truthful research cockpit for NeuroLab AI's maize drought resilience experiment. The interface must never imply that a model generated real crop observations when it only simulated them. Animation is a presentation layer over actual workflow events, not evidence of reasoning or scientific validity. Provide a usable reduced-motion, low-GPU alternative. Preserve a clear distinction among measured data, simulated outputs, hypotheses, and AI suggestions.

## 02. Audience, modes and experience goals

Primary user: agricultural researcher evaluating drought-stress experiments. Secondary: hackathon judges watching a 2–3 minute demo. Research Mode favors accuracy, comparison, provenance, and control. Presentation Mode favors readable full-screen visualization, deliberate pacing, and one-click replay from saved runs. Never hide uncertainties or scientific disclaimers in Presentation Mode. Success: within 10 seconds the viewer can tell what question is being tested, which stage is active, and whether results are simulated.

## 03. Visual identity and design tokens

Aesthetic: high-end scientific instrument, not arcade spaceship. Background #07111D; elevated panels #102233; borders #284457; primary text #E9F3F7; muted text #9CB3C3; cyan signal #4FD7DD; gold discovery #E7B86C; green verified #5CC99B; amber caution #F0BD65; red error #F27D7D. Typography: Outfit or Inter for controls, Zilla Slab for editorial discovery headlines, JetBrains Mono for units, IDs and numeric readouts. Spacing 4/8/12/16/24/32 px; radius 8–16 px. Contrast minimum WCAG AA. Color must never be the only state indicator. Avoid gratuitous neon and illegible microtext.

## 04. Information architecture

Routes: /experiments/new (question and constraints); /experiments/:id/live (live orchestration); /experiments/:id/results (evidence workspace); /experiments/:id/present (cinematic replay); /experiments/:id/provenance (inputs, versions, seeds, artifacts). Persistent navigation: project, run ID, model/dataset provenance, state, export. Core layout: 25% experiment controls, 50% simulation viewport, 25% event timeline and measured outputs on desktop; stacked cards and 2D plots on mobile.

## 05. Pre-run scientific setup

User enters research question, crop, weather range, soil/irrigation constraints, trial budget and dataset/model. Display editable hypothesis, independent variables, dependent variables, controls, fixed assumptions, unit conventions and confidence limits. Require explicit confirmation before execution. Provide demo presets but label them as presets. Never imply a greenhouse sensor is connected unless actual telemetry exists.

## 06. Live stage machine and event contract

Authoritative stages: CREATED → VALIDATING → PLANNING → PLAN_REVIEW → QUEUED → RUNNING → ANALYZING → COMPLETE; alternate FAILED, CANCELLED, TIMED_OUT. Events carry run_id, event_id, sequence, timestamp, stage, public_summary, progress_completed, progress_total, artifact_refs, error_code. Backend emits durable stage changes via SSE; reconnect uses Last-Event-ID or cursor and replays missed events. Progress is determinate only where total work units are known; otherwise use a pulsing activity indicator with elapsed time. No invented percentages or token-by-token 'inner thoughts'. Show public summaries such as 'Selected temperature and irrigation ranges' rather than private chain-of-thought.

## 07. Reasoning visualization choreography

Stage VALIDATING: constraint cards illuminate and unit checks tick on completion. PLANNING: nodes for hypothesis, variables, controls and proposed trials connect as validated structured plan fields arrive. QUEUED: queue depth and experiment count, not fabricated ETA. RUNNING: live trial table, seed IDs, iteration markers and plots update only after persisted results. ANALYZING: baseline comparison and uncertainty ribbons emerge after calculation. COMPLETE: subtle 800–1200 ms discovery reveal; do not animate away caveats. FAILED: stop visuals, display actionable error and retry from a safe checkpoint. CANCELLED: show partial completed trials distinctly.

## 08. 3D scientific scene

Build a maize digital-twin-inspired scene in React Three Fiber. Use an illustrative procedural maize mesh with leaves, stalk, root/soil cross-section and moisture/temperature overlays. Explicitly label 'illustrative plant model' unless geometry comes from measured 3D data. The scene can encode actual model inputs (soil moisture, irrigation level, temperature) with labeled legends; do not morph plant height or biomass to imply measured morphology without validated mapping. Provide orbit, zoom, reset, camera bookmarks, annotations, and 2D fallback. Cap pixel ratio adaptively; dispose geometries/materials; pause rendering when offscreen.

## 09. Scientific charts and evidence views

Required: experiment matrix/table with units; response surface or 2D heatmap for water × temperature; objective-vs-trial plot; baseline comparison (random search vs selected method); uncertainty intervals where model supports them; sensitivity plot; constraint violations. Charts must show axes, units, sample sizes, data provenance and simulation disclaimer. Tooltips expose exact values, trial ID and seed. Provide accessible CSV/JSON download and tabular alternatives. Never show unsupported confidence intervals or statistically unjustified significance stars.

## 10. Results reveal and presentation mode

Storyboard: (1) 0–12 s problem and irrigation budget; (2) 12–30 s experimental design; (3) 30–70 s trial execution and live plots; (4) 70–105 s next-trial selection; (5) 105–140 s baseline comparison; (6) 140–165 s result and uncertainty; (7) 165–180 s reproducibility and Meta role. Presentation Mode must replay real stored event timelines with optional accelerated playback, pause, step, and seek. Clearly show 'replay' vs 'live'. A successful run does not imply field validation. Offer screenshot/export of chart panels without obscuring provenance.

## 11. Motion system and microinteractions

Use Motion for React for UI transitions and shared layout animations; GSAP only for tightly choreographed presentation timeline; R3F for scene animation. Motion tokens: hover 120–180 ms; layout 220–350 ms; panel entry 300–450 ms; scene camera 600–900 ms; discovery 800–1200 ms. Prefer opacity/transform to layout-thrashing CSS. Smooth active-tab indicator glides between tabs; hover highlights transition between adjacent cards; timeline nodes connect as events arrive. Respect prefers-reduced-motion: no parallax, particles, camera orbit or looping pulses; replace with immediate state transitions.

## 12. Performance, responsiveness and resilience

Targets for judge laptop: 60 FPS on capable hardware, graceful 30 FPS fallback; initial interactive shell under 3 seconds on typical broadband after assets cached; main JS and 3D scene lazy loaded; 3D GPU budget tracked rather than assumed. Offer 'Standard / Cinematic' rendering settings with persisted local preference. If WebGL unavailable, display static diagram plus charts. SSE interruptions show disconnected state and reconnect; scientific job continues server-side. Empty, slow, timeout, invalid-input and model-unavailable states must be designed explicitly.

## 13. Accessibility, trust and safety

Keyboard-accessible controls, visible focus, screen-reader announcements for major stage changes (not every token), captions for any narration, pause/replay controls, AA contrast and non-color state indicators. Display model provider, version, prompt/config revision, dataset version, simulation engine, random seed, units and timestamp in provenance drawer. Any AI-generated hypothesis is marked proposed until accepted. Never expose hidden reasoning, secrets, API keys or raw sensitive traces in client events.

## 14. Frontend components and interfaces

Components: ResearchShell, ExperimentSetupWizard, StageTimeline, EventLog, ExperimentGraph, TrialProgress, MaizeScene, SoilLayerOverlay, ResponseSurfacePlot, TrialComparisonChart, EvidenceDrawer, ProvenanceBadge, DiscoveryReveal, PresentationPlayer, MotionPreferences, ErrorRecoveryPanel. TypeScript schemas validated with Zod. Frontend consumes typed /runs/:id and /runs/:id/events endpoints; result artifact URLs signed where appropriate. Charts read persisted numerical artifacts, not synthetic animation fixtures in production.

## 15. Engineering sequence and priorities

P0 (must ship): research shell, validated stage timeline, real SSE events, trial table, 2D heatmap, baseline comparison, results with provenance, reduced-motion state, polished presentation replay. P1 (if time): lightweight 3D maize visualization tied to inputs, scene annotations, camera choreography. P2 (post-hackathon): sophisticated particle systems, volumetric shaders, multiscreen laboratory mode, sensor ingestion, collaborative experiments. Never trade working science for visual complexity.

## 16. Acceptance criteria and test plan

A1: every displayed stage corresponds to persisted backend event. A2: no fabricated percentage, inner reasoning, crop measurement or confidence claim. A3: reconnect recovers ordered events without duplicates. A4: two runs with same inputs/seed/model produce matching deterministic numerical outputs within documented tolerance. A5: all graphs expose units and downloadable underlying data. A6: presentation replay faithfully reproduces stored run and is labeled replay. A7: reduced-motion and no-WebGL modes remain fully usable. A8: error and timeout screens allow recovery. A9: visual QA at desktop, tablet and mobile widths. A10: live demo has offline prerecorded fallback and no hard dependency on network-only animation.

## 17. Codex handoff prompt

Implement this as Document 09 of the current NeuroLab AI hackathon documentation. Read AGENTS.md, Agent_plan.md, Architecture.md and Documents 01–08 first. Audit the repository and propose a minimal component map before coding. Build P0 features in small testable increments, update Agent_plan.md after each increment, and show screenshots plus test evidence. Use the scientific event schema as the sole authority for progress. Do not invent model outputs or scientific data. Defer P1/P2 until core experiment execution and evaluation pass.

## Appendix — MVP demonstration event example

```json
{"run_id":"run-001","event_id":"evt-004","sequence":4,"timestamp":"2026-10-26T17:00:00Z","stage":"RUNNING","public_summary":"Trial 2 of 12 completed","progress_completed":2,"progress_total":12,"artifact_refs":["trial-002"]}
```

**Document authority:** Documents 01–04 govern scientific validity; Document 09 governs presentation and interaction. Where they conflict, scientific validity wins.