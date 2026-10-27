# SonarQube review — 2026-10-27

Local server: http://localhost:9000/dashboard?id=neurolab-ai. Version 26.10.0.133078. The first actual analysis found 217 issues; an initially empty issue list reflected an unanalyzed project, not clean code.

Code repairs include request-model reconciliation, strict implemented-tool schemas, truthful partial terminal status, pending-task tracking, agent/middleware/proxy decomposition, reachable SSE owner/session rechecks, authenticated saved-event retrieval, documented API error responses, finite-number checks, typed Three.js renderer components, native accessible list/group/status/navigation semantics, explicit form-text narrowing, consolidated CSS, contrast corrections, formatting and test assertions that isolate throwing operations.

No application-source exclusion, rule deactivation, quality-gate relaxation, NOSONAR annotation or analyzer whitelist was added. Formatter changes are not scientific contributions. The Three.js adapters preserve renderer props instead of removing supported 3D properties to satisfy a DOM rule.

## Security review dispositions

Four findings are reviewed false positives, with rationale recorded on each server issue. They are not described as code fixes.

| Rule / issue | Rationale and evidence |
| --- | --- |
| python:S3330 / bb3ce08d-ba4c-4200-b28b-4edd730cd03e | The readable cookie contains only the public double-submit CSRF nonce. The separate authenticating refresh cookie is HttpOnly and Secure in production. Header/cookie checks and keyed session-CSRF binding are exercised by auth tests; proxy tests preserve cookie attributes. Making the CSRF cookie HttpOnly breaks its required client-read flow. |
| python:S3330 / 3b72fbec-2160-4126-8012-a91f0836fde6 | The anonymous bootstrap nonce is also non-authenticating, short-lived and double-submit checked. No access/refresh credential is stored here. Same review as above. |
| python:S2245 / 601c74bd-affc-4a5b-86fe-f5507059b618 | Seeded random selection is an evaluation baseline, never a security identifier or secret. Reproducibility is intentional. Authentication uses the secrets module. |
| python:S2245 / 794e7291-b7a4-4faa-8445-b855fa9f2ff4 | Seeded bootstrap sampling is required for reproducible scientific uncertainty intervals. It does not generate credentials. Fixed-seed scientific tests and separate authentication randomness tests cover these uses. |

## Acceptance boundaries

A zero-open-issue result and the quality gate are separate checks. The default gate also requires coverage on new code. Real coverage reports are being supplied; thresholds remain unchanged. No deployed security, live provider scientific acceptance, human accessibility signoff or public-production readiness follows from static analysis.
