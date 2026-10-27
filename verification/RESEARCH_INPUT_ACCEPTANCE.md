# Research input acceptance — editor verified; live science gates separate

Audit date: 2026-10-27. This replaces the earlier assumption that backend foundations meant the editor task was complete. The actual-browser editor gate is recorded below. This does not prove that every requested scientific analysis or live Meta integration is complete.

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Root-cause audit | Original HTML cap was 2,000; backend request migration/syntax defects also prevented reliable execution. Documented in the editor guide and BUILD_LOG. | Verified |
| Short / 5,000 / 20,000 characters | API tests save, retrieve and execute actual numeric-tool runs; compare the full original in draft, run and report. Includes multiline Unicode/Markdown. | Automated pass |
| Exact text and formatting | Source string is not trimmed on submission; CRLF/newline and Unicode API fixtures round-trip exactly. Frontend tests compare the full textarea string after saved-draft restoration. | Automated pass |
| Clear over-limit behavior | 20,001-code-point input stays visible; save/run is blocked; 20,000 emoji code points are accepted by the editor. | Automated pass |
| Owner-scoped drafts / stale updates | Separate accounts see separate drafts; owner-forgery body rejected; stale expected revision returns 409 and preserves the newer saved draft. | Automated pass |
| Draft refresh and save races | Remount restores server draft; typing during an in-flight save remains marked unsaved; stale-save errors preserve local text. | Automated pass |
| Expandable editor | Native dialog shares the original, closes and restores trigger focus in DOM tests. | Automated pass; browser expanded dialog observed |
| Structured configuration | Optional collapsed fields map to typed server configuration; execution uses accepted supported methods and budgets. | Automated UI configuration matrix pass |
| Refinement review | API proposal endpoint and server schema validation; UI original/proposal comparison, editing, acceptance and stale-write protection. | Contract/UI tests pass; live provider pending |
| Context management | Original stored once; structured context and pending tasks used after initial selection; schema-inclusive conservative token guard rejects overflow without truncation. | Automated tests; live provider pending |
| Original / refined / completed tasks inspection | Reports include the persisted plan/configuration and a UI inspector with evidence IDs. Historical reports without plans are explicitly identified. | Automated pass; browser original/task inspector observed |
| XSS | Script-like objective text remains text; no raw HTML rendering; DOM test checks no injected script element. | Automated pass |
| Real browser: 20,000-character submit / persist / retrieve / numeric execution | Chrome via CUA; run `c86c9fc4-2c0d-41f8-b282-b23ed64411cd`; authenticated save, real reload, exact full value restored, numeric dataset profile completed. Independent DB comparison proves draft/run/report equality, 20,000 characters, one artifact and 864 observed records. See `research-input-browser.json`. | PASS |
| Real browser: supplied full scientific objective | Not yet run on the completed editor. Missing scientific-tool requirements remain separately tracked. | PENDING |

The numeric-run tests use the immutable Ghana source with a supported profile tool. They prove input integrity and actual computation, not that every arbitrary scientific request is supported or scientifically answered. The Meta adapter fixtures are contract mocks, not live model evidence.

## Browser-discovered defect and correction

The first browser save exposed missing PUT/PATCH exports on the Next BFF, returning HTTP 405 despite successful backend/component tests. Both route methods were added and dedicated proxy tests exercise identity/CSRF/body forwarding. The real-browser save/refresh/run path was then repeated successfully. This finding is why component mocks alone were not used for completion.

Latest local gate before final evidence commit: 61 Python tests, 8 proxy tests, 35 UI/authentication/renderer tests, source audit, lint/typechecks and optimized build passed. Sonar analysis 2026-10-27 16:45 UTC: 0 open issues, quality gate OK, 81.2% new-code coverage. Changes after that scan require revalidation.

Focused actual-browser responsive checks: the 390×844 viewport had document width 390px; the expanded dialog measured 358×812px. Escape closed the writing dialog and restored the Expand trigger focus. The mobile navigation opened, closed with Escape and restored its trigger; no open dialog remained. The temporary viewport override was reset. This is not a complete screen-reader or cross-device signoff.
