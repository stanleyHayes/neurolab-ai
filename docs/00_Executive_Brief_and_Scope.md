# 00 — Executive brief, scope and scientific claim boundary

**Pitch:** NeuroLab AI is a Meta-powered autonomous research agent that designs, runs and evaluates reproducible computational analyses of African maize drought-response field trials. It identifies promising *research hypotheses*, quantifies uncertainty and selects which analysis to run next. It is not a field-tested agronomic recommendation engine.

## Primary user
Agricultural researcher, plant breeder or graduate student with trial data and limited statistical automation. Demo journey: select Ghana dataset -> ask 'Which genotypes retain yield under managed drought, with stable performance across trial years?' -> agent creates falsifiable hypothesis -> calls validated analysis tools -> receives measured outputs -> selects follow-up comparison -> displays evidence and limitations -> exports reproducible report.

## P0 acceptance
1. Actual Ghana records are loaded, lineage retained, and conditions/years/genotypes can be explored.
2. Agent executes 2 or more genuinely result-dependent tool decisions using Meta tooling.
3. Numeric outputs reproducible with fixed seed and source SHA-256.
4. Statistical uncertainty and design caveats displayed.
5. Demo live in under 3 minutes; open public code; new work clearly distinguished.

## P1
IITA independent pattern replication (not identical-genotype validation), Meta open-weight eligible serving, NASA weather context, visualization polish.

## Exclusions
Unvalidated irrigation recommendations, unsupported causal claims, autonomous wet-lab actions, commercial crop forecasts, medical/political use cases, speculative dataset merges.

## Research question and success criteria
Question: What genotype-by-water-regime patterns in observed field records justify further breeding trials? Success: grounded analysis, traceable evidence, honest uncertainty, useful follow-up experimental design; not 'proving' superior genotypes from small observational comparisons.
