# Cinematic replay and research setup — 2026-10-27

## Requirements and delivered code

Documents 07 and 09 require a truthful presentation layer over persisted execution, prominent replay labeling, controls for pause/step/seek/speed, source and uncertainty visibility, and reduced-motion/no-WebGL alternatives. The player is reachable on `/live-experiment`, with a direct link from results and from research setup. It uses the existing authenticated run loader; it does not make inference or analysis requests.

The three-column cockpit contains the original objective and provenance, a stage/illustrative maize viewport with measured-evidence reveals, and selectable recorded event chapters. Open cinematic view expands it into an accessible dialog. Playback has restart, play/pause, next-event, keyboard/pointer seek and 1×/2×/4× presentation pacing. Timing is explicitly a readable 1.8 seconds per event at 1×; the original timestamps remain visible. Playback stops at the end or when the document is hidden. Reduced motion disables autoplay and 3D while retaining manual navigation. Scene rendering preference alone is stored locally. The existing maize model is reused, not newly claimed scientific simulation.

Artifact reveals require a prior `tool.completed` event for the artifact and the recorded source hash. Seeking backwards hides future artifacts. Other runs' events are filtered, and duplicate sequences are ordered/deduplicated. The measured contrast retains units, sample size and its actual bootstrap interval. Candidate means remain descriptive and caveated. Original report/artifacts/events can be exported. Water/temperature response surfaces, crop growth predictions and unsupported benchmarks are not fabricated to fill the storyboard.

The research setup now has compact icon actions, an organized optional-configuration disclosure, compact analysis mode cards, a separated launch action and a source-integrity footer. Model/refinement controls use an authenticated capabilities response and fail closed if availability cannot be verified. Unavailable draft storage has a useful recovery message while preserving writing. A missing account draft remains a successful revision-zero API response, not an error.

## Credit pause and runtime repair

`MODEL_INFERENCE_ENABLED=false` in the ignored local `.env` pauses inference without erasing past smoke-test verification. Both API entry points and the adapter transport check the pause; deterministic tools and saved replay remain usable. `.env.example` documents the switch. Tests demonstrate that even a previously created adapter cannot contact the provider while paused.

The pre-existing API on port 8000 was confirmed to belong to this checkout and to lack `/research-draft` (HTTP 404). It was restarted with its exact existing environment, database and command, with inference paused. The route now returns HTTP 401 to an unauthenticated request, establishing that it exists and remains protected. No database, owner or credentials were replaced. The isolated review service on 8107 also reports inference paused. Authenticated draft behavior is verified in API tests; an owner's production account was not impersonated.

## Acceptance boundary

Automated evidence is recorded in BUILD_LOG.md. Browser automation currently reports that browser access is unavailable. No new cinematic/setup screenshot, visual QA, live GPU performance figure or full accessibility signoff is claimed for this milestone. The earlier results-redesign screenshots cover that previous milestone only. Browser verification remains required when access returns. The full scientific objective, trait/stability methods, provider spend controls and production/deployment/publication gates remain open.

A subsequent authenticated runtime check on the isolated review API verified inference disabled, saved draft revision 2 with exactly 20,000 characters still preserved, two owned saved runs, and three accessible real artifacts on the latest COMPLETE run. This check used the existing disposable local review account and performed no new research/model execution. The primary port-3000 studio returned HTTP 200 with the redesigned heading and deterministic-mode copy; its BFF correctly required authentication for capabilities.

## Source provenance follow-up

The source card was redesigned from the owner's additional screenshot: three actual-data metrics, citation/license and observed regime counts, a separate exact-byte identity panel, source-hash copy feedback, explicit selected-run matching and visible scientific limits. Four dedicated UI tests cover counts/citation, clipboard success/failure, source mismatch and unavailable data. The complete expanded quality run passed 127 tests (64 Python, eight proxy, 55 UI), lint/types/data integrity and build. Browser visual acceptance is still pending. Generated scanner working files are now excluded from ESLint alongside other build artifacts; application source coverage remains unchanged.

Final full-source SonarQube analysis at 17:40 UTC passed the unchanged quality gate with zero new violations/open issues and 82.4% new-code coverage. The final source-card spacing finding was fixed; lint, TypeScript, all 55 UI tests and the production build passed again. No rule suppressions, application exclusions or reduced thresholds were used.
