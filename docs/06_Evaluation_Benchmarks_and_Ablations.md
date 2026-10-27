# 06 — Evaluation and benchmarking

## Primary measurement
Task completion accuracy on 12 prewritten scientific questions; groundedness of claims against computed outputs; proportion of valid tool calls; reproducibility; runtime; inference cost. Record all failed trials. Do not select only favorable examples.

## Agentic usefulness
Create 10 fixed tasks with objective and limited tool budget. Compare (A) Meta autonomous selection, (B) deterministic heuristic next-tool selection, (C) seeded random allowed tool selection. Equal data access, step/time budget, scoring rubric. Score whether an action resolves uncertainty in the target hypothesis and whether the final conclusion is justified. Have blind human reviewer score usefulness where feasible; clearly mark subjectivity.

## Ablations
Meta agent with vs without feedback from previous tool outputs; Meta vs fixed workflow; Ghana-only vs optional IITA contextual evidence. No cross-source pooling without valid comparability. If simulation later added, benchmark against random search and Bayesian optimization with equal calls, multiple seeds, confidence intervals.

## Safety tests
Malformed JSON, prompt injection in a dataset cell, impossible hypotheses, zero denominator, missing year, duplicated observations, nonconvergent model, rate limits, model outage, non-unique join keys, dataset hash mismatch.

## Evidence
Save `eval/tasks.json`, `eval/results.jsonl`, report with mean and confidence interval, model ID, commit SHA, timestamp and spend. **Do not claim winning metrics before running.**

## 2026-10-27 recorded-answer increment

[Recorded-answer evaluation](RECORDED_ANSWER_EVALUATION.md) adds actual offline question/policy runs, preserved failures, trace audits and evidence-bound review scoring. Non-blind assistant ratings are available; no live Meta, blind-human review or feedback ablation has been completed. Action coverage remains distinct from answer quality.
