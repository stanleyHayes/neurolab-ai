# Provider spending-control review — 28 October 2026

Meta's [official spend-alert documentation](https://dev.meta.ai/help/billing/spend-limit-alert) describes a notification threshold rather than an enforceable provider spending cap. A configured alert must not be reported as a hard limit. Actual account-alert settings have not been inspected in this review.

NeuroLab's SQL reservation guards enforce the configured application/owner/run ceilings before transport. Their scope is the shared application ledger, not unrelated uses of the same provider account or key. Unknown calls retain reservations; amounts are not invoices. [Usage documentation](https://dev.meta.ai/help/usage-and-limits/api-usage) explains the provider dashboard and response accounting; per-response records do not reconcile a whole account bill.

The future evaluation approval must document the provider's available controls and their limits, actual application budgets and any unverified account settings. It must not wait for or claim a nonexistent provider hard-cap setting. No application limit was raised or removed by this review, and the frozen matrix remains unapproved/unexecuted. Public-production billing/readiness gates remain open. Correct the review/preflight contract and freeze a current protocol before paid matrix collection; do not silently toggle an unsupported-cap flag to claim protection.
