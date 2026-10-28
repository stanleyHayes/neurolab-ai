# Seed-aware scoring of preserved live-matrix answers

This is a scoring tool, not a completed evaluation. No180-trial live collection or independent human review is claimed.

```sh
python3 -m scripts.score_live_evaluation \
  --records /private/collection/results.jsonl \
  --reviews /private/collection/bound-reviews.json \
  --output /private/collection/new-summary.json
```

Use exact evidence-bound reviews from the policy-masked packet tool. The output is exclusive; an existing summary is never replaced. The offline scorer continues to refuse live policy names. Do not feed synthetic test ratings into a real comparison.

## Denominators and missingness

The scorer validates exact catalog questions, seeds, five policies, unique matrix cells, two-call budgets, report objective/seed consistency and answer/evidence digests. It retains partial collections and reports missing cells separately; an incomplete collection cannot silently become a complete matrix.

- Reportless attempted failures receive automatic0 for direct answer and usefulness, explicitly distinguished from a reviewer rating. Positive direct/usefulness reviews of a missing answer are rejected.
- Claim support and scope honesty are assessed only where an answer exists. Reportless trials are excluded with explicit counts; this is output-conditional quality, not end-to-end reliability.
- Successful outputs awaiting review remain null, not0 or1. Unattempted trials remain missing, not observed failures. A question mean is null if an eligible seed is missing or awaiting review.
- No overall mean/interval is produced for a dimension while eligible question scores remain missing. Every excluded reportless trial, pending review and absent matrix cell remains visible. A completely reportless question is ineligible for support/scope; it remains a zero for direct answer/usefulness.

Each policy includes all twelve accuracy questions and the predeclared first ten usefulness questions. Reports retain all three per-seed values and their rating basis. Workflow PARTIAL status is not automatically a semantic failure; exact written answers/evidence require review.

## Question-level descriptive uncertainty

First average the declared seeds within each question. Give eligible question means equal weight. Compute the exact distribution of resampling whole question means with replacement, keeping the resample size equal to the number of eligible questions. Integer weights count possible sequences through dynamic convolution of exact rational question means. Report inverse-CDF2.5/97.5percentiles. No random generator or finite Monte Carlo approximation is used. Seeds never become independent questions. The interval describes rating variability conditional on this small fixed known set; it is not a population-accuracy interval, independent scientific validation or evidence that one policy wins. Related questions, known implementation prompts, subjective judgments and reviewer effects remain limitations. Scores do not establish held-out performance.

A separate test makes every question's three seed ratings1/0/0: all question means are1/3, so question-resampling uncertainty is degenerate at1/3. Resampling individual seeds would manufacture a different uncertainty estimate. Those values are solely synthetic test fixtures.

## Operational evidence and review identity

Observed model calls, actual recorded reservations/outcomes, elapsed time, all-record tool requests/artifacts and report trace-audit coverage remain separate. Missing count/reservation records produce null totals with known subtotals, not invented zero usage. Reservation totals are conservative spending admissions, not invoices; billed USD stays null. Citation/schema/source agreement is trace validity, not prose entailment.

Reviewer type and claimed blinding are reported. Independence is never certified merely by reviewer metadata, and no winning policy is selected automatically. Independent human review, actual matrix execution, verified billing/provider controls and provider cancellation remain open gates.
