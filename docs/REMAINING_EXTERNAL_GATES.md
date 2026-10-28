# Remaining external gates — 28 October 2026

The application is a working, invite-gated research prototype. This handoff does not certify production agronomy, independent scientific validity or a submitted hackathon entry. The [current acceptance audit](../verification/PROJECT_ACCEPTANCE_AUDIT_2026-10-28.md) remains the detailed ledger.

## 1. Hosted inference resolved through Baseten; direct Meta remains historical

**Current serving gate closed:** actual hosted Baseten run `c8591707-1b97-41b9-badf-b94ca1df7ff8` completed the original objective with six real model selections/six tools and no recovery on97fce76. [Baseten proof](../verification/baseten-activation-2026-10-28/original-proof.json).

**Needed only if returning to direct Meta API:** provider/account investigation of the historical404 below. No support message has been sent.

The last recorded one-action hosted diagnostic was `e4a93800-5505-4735-9736-8c1b4bac5d23`, created at 2026-10-28 01:35:58 UTC. Render API and worker reported scientific/backend commit `ebf1111ba5f13c1fb874203cf2b93dc88946e569`. Model `muse-spark-1.3` returned HTTP 404; the adapter stopped further provider requests and retained one explicitly labelled deterministic recovery artifact. Its status is PARTIAL, with no successful Meta selection.

Earlier bounded diagnostics reported `model_not_found`; catalog results differed between local and hosted environments. The underlying cause has not been established. Local real Meta execution subsequently succeeded in the complete 180-trial comparison, including 144 HTTP 200 responses. This does not prove hosted availability or establish a geographic, billing or credential explanation.

A provider/account operator can investigate:

- Whether the existing workspace/key is entitled to this model from the hosted runtime.
- Whether that workspace requires a different documented endpoint or model identifier.
- Whether provider-side request/access logs explain the hosted 404 at the recorded UTC time.

Share only sanitized run/time/model/status information. Do not include API keys, `.env`, passwords, access tokens, refresh cookies or private signing material. Do not use a proxy or region change to evade an access restriction.

**Evidence required before returning to the direct Meta path:** a bounded real hosted response, followed by the same owned original-objective investigation with actual Meta selections and tool-derived outputs, retained raw/sanitized evidence and no relabelling of fallback as successful inference. Health flags, model catalog entries and fixture responses do not close it. Avoid more paid retries until there is new provider/configuration evidence.

Sources: [recorded deployed diagnostic](../verification/model-rationale-deployment-2026-10-28.json), [historical engineering addendum](../verification/HOSTED_META_ACTIVATION_ADDENDUM.md), [actual local comparison](LIVE_COMPARISON_2026_10_28.md).

## 2. Independent human answer review

**Needed from:** an identified human reviewer; assignment was requested from the owner and remains pending.

All 180 actual answers are preserved. The review ZIP contains the policy-masked packet, empty template and existing rubric; its confidential mapping is excluded. The packet and mapping have been checked against the original answer/evidence hashes. No ratings have been supplied or invented.

The owner holds `NeuroLab-Human-Review-Packet.zip` in the private collection's `independent-review` directory. Provide that ZIP to the chosen reviewer without its mapping or operational policy comparison. The reviewer returns the edited template with all four binary ratings, identity/type, rationale, truthful blinding and prior-exposure fields. Masking does not itself establish independent or blind review.

**Evidence that closes the review gate:** real completed reviews bound to the unchanged packet and source records, validated by `bind_packet_reviews`, then scored using `scripts.score_live_evaluation`. Retain all failures and unreviewed/missing counts. Do not substitute workflow completion, tool coverage, citation existence or assistant ratings for the declared human assessment. Do not claim held-out performance or a winner merely because the scorer accepts the records.

Sources: [actual collection verification](../verification/live-matrix-actual-2026-10-28/verification.json), [unreviewed summary](../verification/live-matrix-actual-2026-10-28/summary-unreviewed.json).

## 3. Demo delivery and submission

**Needed from:** the owner/entrant and, where necessary, the organizer.

The local 165.53-second narrated MP4, subtitles and editable project are delivered and verified. A person still needs to listen to the generated narration. No public video upload or entry submission has been performed.

Before submission, confirm the track, representative/contributors, actual event eligibility and reuse disclosures, official live deadline, destination for public video and entry details. Verify the final public video and live product from a fresh private browser, then retain the actual receipt and final source revision. Historical checklist dates are not a current organizer confirmation. Do not invent team, eligibility, impact or submission evidence. Optional prize tracks remain optional.

Sources: [video delivery brief](demo/video/BRIEF.md), [submission checklist](15_Submission_Checklist.md), [new-work record](../BUILD_LOG.md).

## 4. Production-only operational gates and deferred work

Keep invite gating and the prototype status. Actual target key distribution/retirement, managed recovery cutover, monitoring/alert recipients, exhaustive security/accessibility and hosted live-provider cancellation remain scoped gaps; local fixtures and logical restores do not prove them. Use the existing deployment and signing-key runbooks before an operational change, rather than rotating keys ad hoc on a running service.

Scheduled encrypted offsite backups were explicitly deferred by the owner. R2 setup and a round trip are preparation, not an active schedule or retention policy. Record this as future work; do not activate it or treat its deferral as a newly discovered application defect.

Independent field validation, safe IITA comparability, calibrated crop simulation and optional model/prize tracks are not delivered scientific claims. Actual live CSV-cell injection resistance is also unverified; the known-question comparison does not replace that test. None of these gaps should be hidden by changing acceptance definitions.
