# Frontend / UI Acceptance Review

**Audit date:** 2026-10-26  
**UI requirement source:** `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/docs/09_Cinematic_Scientific_Visualization_and_Interaction_Design.md` and `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/docs/11_Test_Plan_and_Acceptance_Criteria.md`.

## Architecture and routes

- Next.js 16.4.3 App Router, React 19.3.1, TypeScript 6.0.3.
- `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/research-workspace.tsx` is the shared interactive client workspace. `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/[section]/page.tsx` defines 11 detail destinations; `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/app/page.tsx` serves Overview.
- Route smoke served optimized production app on loopback. All 12 planned app routes returned HTTP 200 with expected section title and shared navigation.
- Navigation destinations: Overview, Experiment Studio, Live Experiment, Research Results, Genotype Explorer, Trait Analytics, Environments, Data Library, AI Insights, Next Experiments, Reports, Settings.
- Shared shell contains grouped navigation, sidebar state, route-specific sections, persisted backend histories and artifact data.
- Existing Chrome headless screenshot artifacts were found in `/tmp/neurodyne-live-shots/`: 12 desktop route captures at 1600×1050 and two mobile captures at 390×844. Representative Overview, Live Experiment and Data Library mobile images were inspected. This is limited visual evidence, not an assertion that every interaction/render state passed.

## Data and progress truth

- Frontend fetches `/api/datasets/ghana_combined/profile`, `/api/research-runs`, run/report/artifact and SSE endpoints.
- Charts/summary panels consume stored result artifacts; observed regime/gene values are not embedded in TSX as fixed measurements. UI includes descriptive/observational caveats, data DOI, license and source hash.
- Live event consumer reads backend SSE frames, tracks event sequence, attempts cursor reconnect and loads persisted reports/artifacts. Replay and provider mode labels are distinguished.
- Loading skeletons, retryable error panels, empty states, reduced-motion preference, keyboard navigation for saved-event scrubber and `aria-live` announcements are present in source.
- **Live-run caution:** Backend `hypothesis.proposed` event uses a fixed summary. UI labels it as a hypothesis event and can give the impression a hypothesis was generated when there is no model-generated falsifiable hypothesis in the actual trace. Partial reports also receive `run.completed`, so timeline status may visually imply full success.
- User interaction sends run settings from UI but hardcodes seed 2026 and max step/call/time values in `runAnalysis`. Controls for environmental constraints, crop/weather ranges, or confirm/review plan specified by the 3D simulation design do not exist; these optional simulation controls are not part of current Ghana analysis MVP.

## Planned page acceptance table

| Page | Response | Code-level evidence | Acceptance verdict |
|---|---|---|---|
| Overview `/` | HTTP 200 | Overview hero, Ghana workspace and calls to action. | **PARTIAL:** server route verified; visual/keyboard controls not browser-tested. |
| Experiment Studio `/experiment-studio` | HTTP 200 | Research question textarea; replay/Meta mode choice; start/cancel actions; bounded run request. | **PARTIAL:** source controls and request plumbing exist; live browser action not executed. |
| Live Experiment `/live-experiment` | HTTP 200 | Persisted SSE timeline, saved run reload/replay controls. | **PARTIAL:** backend event run works; UI has not been run against the real experiment in browser. Completion/hypothesis labeling is a defect. |
| Research Results `/research-results` | HTTP 200 | Backend artifact-driven contrast/ranking panels; JSON/index CSV export. | **PARTIAL:** route and code inspect; chart values not browser-compared against API response. |
| Genotype Explorer `/genotype-explorer` | HTTP 200 | Shows descriptive genotype artifact rows and warnings. | **PARTIAL:** rankings descriptive only, no stability/uncertainty; no browser data verification. |
| Trait Analytics `/trait-analytics` | HTTP 200 | Observed yield summaries and limitations. | **PARTIAL:** no trait association tool/correlation chart verified. |
| Environments `/environments` | HTTP 200 | Regime contrast and confounding caveat. | **PARTIAL:** only three ENVT strata; not cross-environment stability or calendar years. |
| Data Library `/data-library` | HTTP 200 | Ghana provenance, DOI/license, hashes, row/genotype profile. | **PARTIAL:** IITA sources are not surfaced as analysis-ready datasets in app. |
| AI Insights `/ai-insights` | HTTP 200 | Only evidence-linked grounded claims rendered. | **PARTIAL:** real report claims link artifacts; no answer-quality validation; live trace lacked the requested scientific finding. |
| Next Experiments `/next-experiments` | HTTP 200 | Reuses experiment brief UI. | **PARTIAL:** no actual backend-selected evidence-based experiment design. |
| Reports `/reports` | HTTP 200 | Reproducibility/report export presentation. | **PARTIAL:** report includes run seed/source/evidence, but no Git commit and incomplete research workflow. |
| Settings `/settings` | HTTP 200 | Reuses setup mode and objective controls. | **PARTIAL:** no identity-provider, user, provider quota, or user-level account settings. |

## UI defects / unknowns

- The existing project dependency tree does not declare Playwright/Puppeteer/Selenium; a preinstalled external Playwright package and browser were used for a task-scoped smoke check. This does not replace a maintained in-repository test suite or the full acceptance matrix.
- No automated assertion that chart values equal API artifacts, controls do intended action, saved-run replay works in a browser, or error/reconnect states are usable.
- Full keyboard-only navigation, screen-reader, contrast/WCAG, broad tablet/1080p viewport, async provider, and complete interaction acceptance remain outstanding. Task-scoped Playwright smoke checks for scene keyboard buttons, reduced-motion fallback, and one 390px mobile viewport were run, but are not full product acceptance.
- The inspected Live Experiment screenshot shows the backend empty-events state (“No saved events yet”) while one saved run appears in the list; it does not show an opened run timeline. This is a static default-state capture, not evidence of live run playback.
- Product run route is a shared client with no login. The app's global run history is not isolated by end user.
- `presentation` playback advances through actual event array and is labeled replay; no fake scientific measurements were observed in source. Nonetheless, actual interaction/animation behavior is unverified.
- A `hypothesis.proposed` label appears for a fixed backend summary; current trace does not support the impression of a model-generated scientific hypothesis.
- Long objective field, mode controls, cancellation, event replay, export download, navigation group collapse/expanded state were not clicked/tested in a real browser.
- The overview includes a lightweight, decorative R3F maize-and-soil scene with orbit/zoom/reset and an SVG fallback; it is explicitly labeled illustrative and not measured morphology. This is not a crop simulation and conveys no measured plant traits. Task-scoped Playwright check: desktop WebGL canvas rendered at 532×276 with no page errors; all seven explicit camera controls were present, and rotate/tilt/zoom/reset clicks completed; reduced-motion and 390px mobile both rendered the static illustration without a WebGL canvas; mobile document width equaled the 390px viewport. WebGL-disabled fallback was verified in code but not forced in browser. Screenshot appearances were inspected at desktop/mobile. These scoped checks do not certify cross-browser visual quality, keyboard focus sequences, or full accessibility.

## UI verdict

**Routes/build: verified. Functional browser acceptance: not verified.** Pages are workspace views rather than 12 independently data-rich products, and several category pages reuse a shared panel. A demo recording should not be made until the actual full-stack live run is observable in a browser and its event/recommendation content is corrected and scientifically accepted.