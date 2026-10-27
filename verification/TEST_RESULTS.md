# Verification Test Results

**Date:** 2026-10-26  
**Workspace:** `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai`  
**Rule:** This report records direct current-run results. It does not convert source inspection or historical `BUILD_LOG.md` entries into current execution evidence.

## Automated checks

| Command | Result | Actual observation |
|---|---|---|
| `make quality` | **PASS (exit 0)** | Ruff lint/format, ESLint, TypeScript, Python tests, manifest audit, Python compile, optimized Next.js build. Re-run final wrapper wrote `MAKE_QUALITY_EXIT=0`; **34 Python tests** ran and reported `OK`. |
| `python3 scripts/audit_datasets.py` | **PASS** | All manifest hashes and physical CSV row counts matched. Ghana combined 864; drought and well-watered each 432; IITA irrigation 337,913 physical with 336,953 fully-empty. |
| `python3 scripts/normalize_ghana.py` | **PASS** | `Normalized 864 source records; sha256=2e37c07f30e00efb33b59954dd6d02a04f3d67349790d782b70dbedfdaff05bc; unit=kg/ha; quarantined=0`. |
| `python3 scripts/prepare_data.py` | **PASS** | `input_rows=337913`, `fully_empty_rows_removed=336953`, `output_rows=960`; notes no other rows filtered/no regime joins/no unit inference. |
| `npm audit --audit-level=high` | **PASS** | `found 0 vulnerabilities`. |
| `python3 -m pip check` | **PASS** | `No broken requirements found`. |
| `python3 scripts/smoke_meta_provider.py` | **PASS (real provider request)** | `PASS: provider responded with structured JSON for model 'muse-spark-1.3'.` Key value not printed. |
| `python3 scripts/run_evaluation.py --seed 2026 --budget 2` | **PASS (fixture baseline only)** | Fixed workflow selected target tools in 6/12 tasks; seeded random 3/12; deterministic replay 6/12. Script output says no LLM answer quality is scored and Meta comparison not run. This is not evidence of live Meta performance. |

### `make quality` details

- Ruff: passed lint and format checks (`18 files already formatted`).
- ESLint: passed with `--max-warnings=0`.
- TypeScript: `tsc --noEmit` passed.
- Unit tests: latest rerun `Ran 34 tests in 4.223s`, `OK` (an earlier audit run was 4.788s).
- Data audit: `PASS: manifest integrity and source row counts`.
- `py_compile neurolab/*.py scripts/*.py tests/*.py`: passed.
- Next.js optimized production build: passed; Next.js 16.4.3; static/SSG routes include `/`, `/experiment-studio`, `/live-experiment`, `/research-results`, `/genotype-explorer`, `/trait-analytics`, `/environments`, `/data-library`, `/ai-insights`, `/next-experiments`, `/reports`, `/settings`; dynamic proxy `/api/[...path]`.

## Direct functional checks

| Check | Result | Notes |
|---|---|---|
| 12 workspace route HTTP smoke | **PASS (HTTP only)** | Production Next server on loopback returned HTTP 200 on all 12 routes; expected title text and shared navigation present. This is not browser interaction acceptance. |
| Ghana component-vs-combined check | **PASS** | Both 432-row component files match corresponding combined-regime records by genotype, ENVT, REP, BLK, and YIELD. The app analysis loader only loads the combined file. |
| Independent genotype ranking | **PASS arithmetic / PARTIAL scientific method** | Independent equal-environment means produce identical ordering of all 72 genotypes. This does not validate a breeding recommendation or infer stability. |
| Independent drought retention calculation | **PASS arithmetic** | `100 × 1230.2687815072015 / 2616.0414647785037 = 47.0278777332517%`; matches tool result. Observational and environment-confounded. |
| Independent cluster-bootstrap interval | **PASS arithmetic** | Raw CSV resampling of BLK within CONDITION × ENV × REP for 500 iterations, seed 1001, exactly matched tool bounds `[-1559.5278377901084, -1205.0839275256822]`. |
| Reproducibility | **PASS for deterministic descriptive tool** | Two `compare_regimes` runs with seed 1001 / 500 bootstrap samples returned equal results; unit test also repeats seeded contrast. |
| IITA row cleaning | **PASS for removing fully empty rows only** | Output 960 rows and retained `unnamed_column_3`; raw source hash unchanged per audit. No scientific analysis on these rows is available. |
| Browser screenshots | **PASS (limited visual evidence)** | Existing Chrome headless artifacts: 12 desktop screenshots (1600×1050) and two mobile screenshots (390×844), dated Oct 26; representative Overview, Live Experiment and Data Library-mobile images were inspected. Artifacts are under `/tmp/neurodyne-live-shots/`, not repository files. |
| Browser interactions/accessibility | **NOT RUN** | No Playwright/Puppeteer/Selenium package. Static screenshots do not test buttons, saved-run loading, keyboard/screen-reader behavior, chart/API value correspondence, or live experiment execution. |
| Docker build | **NOT RUN / NOT CONFIGURED** | No Dockerfile or compose file exists. Docker binary presence does not provide a build configuration. |
| Real deployment/TLS/backup/restore | **NOT RUN** | No deployment configuration or target environment supplied. |
| Full API + frontend live Meta run | **NOT RUN** | Direct backend agent run was executed with a real Meta adapter and in-memory SQLite. Route tests are deterministic unit/API tests; the Next proxy was not connected to a live run during browser interaction. |

## Meta error behavior evidence

- Real smoke success: verified above.
- Real invalid credential test: **NOT RUN** to avoid mutating local key configuration / accidentally invoking repeated account auth failures.
- Real model-unavailable, real provider timeout, billing/credit exhaustion, and production missing-key API tests: **NOT RUN**.
- Missing env validation and provider HTTP error/timeout sanitation have unit tests in `tests/test_agent_tools_api.py`; fake transport probes were attempted during this audit but shell command input was mangled and no standalone result is claimed. The test suite's pass is evidence only for the cases it actually covers.
- Historical `BUILD_LOG.md` reports a direct HTTP 401 for an unauthenticated Meta request; that is prior recorded evidence, not independently repeated during this audit.
- A Chrome binary (`Google Chrome 155.0.8059.85`) and prior screenshot artifacts were found after initial package/command checks. The earlier statement “no browser executable” was incorrect; it referred to no browser runner in PATH. Visual screenshot evidence is included above, but no interaction acceptance is claimed.

## Test command/output notes

An initial `make quality` wrapper used the reserved zsh variable `status`, so that wrapper exited before capturing its return code. The quality command itself completed all stages in its log; it was rerun with `rc` and the final marker was `MAKE_QUALITY_EXIT=0`. This is a harness mistake, not a product test failure.

An initial live agent runner heredoc and two Python instrumentation probes were mangled by the shell integration, so no result is claimed from those failed invocations. The live-agent test was rerun successfully via a single `python3 -c` invocation; its run outcome is documented in `AGENT_EXECUTION_TRACE.md`.