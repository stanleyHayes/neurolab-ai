# NeuroLab AI submission form answers

Updated 29 October 2026 after hosted hackathon-model verification. Replace the video URL with your final uploaded link; credentials belong only in private judge access notes.

## Team Name

NeuroLab AI

## Team Members

Stanley Hayford — sahayford

## Track

Indie Developer Track

## Problem statement

Push the Frontier

## Most Viral Track X post link

Leave blank unless entering this optional award with a qualifying published post.

## Project Description

NeuroLab AI is a scientific research prototype that helps researchers investigate drought-related patterns in published Ghana maize trial data. It connects a research objective and reviewable analysis plan to bounded Meta-guided tool execution. Researchers can inspect genotype rankings, water-regime comparisons, trait associations and environment sensitivity, then choose a follow-up analysis or stop when the data cannot support a stronger conclusion.

The project addresses a practical problem: a convincing AI narrative can be difficult to distinguish from an analysis grounded in measurements. NeuroLab AI retains source lineage, model decisions, computed artifacts and scientific limitations in saved runs and exportable reports. Charts and cinematic replay reflect actual recorded results and events; deterministic mode is explicitly labelled and makes no model calls.

On October 29, a judge-account investigation completed using the required Baseten-hosted Meta model, meta-models/muse-spark-open-1026, with six real model selections, six scientific tools and six result artifacts, without recovery. An earlier exact-model attempt rejected one invalid model response, used a labelled recovery and remained PARTIAL; both attempts are retained. The current Ghana dataset contains 864 plot records covering 72 genotypes. Findings are exploratory, water regimes are confounded with environments, and the application does not provide validated field recommendations.

## Public GitHub Repository

https://github.com/stanleyHayes/neurolab-ai

## 3 Minute Demo Video

Insert the public YouTube URL of the latest reviewed export. Use NeuroLab-Hackathon-Final.mp4. The final model-status revision replaces the earlier video's obsolete statement that the hackathon alias is unverified. Check the actual uploaded version, captions and signed-out playback before submitting.

## Describe your use of Meta products to build the submitted project

NeuroLab AI uses Meta models to propose the next permitted analysis action from the research objective, accepted plan and prior computed evidence. The direct Meta Model API path has recorded Muse Spark 1.3 executions and a separate evaluation containing 72 real-model trials. The current hosted application uses Meta Muse Spark Open through Baseten with the hackathon identifier meta-models/muse-spark-open-1026 and the separately emailed hackathon key.

Model proposals are structured and validated on the server against JSON schemas and an allowlist. The Baseten adapter forces a named function response and validates its arguments before dispatch. Python tools calculate the numerical findings; the model does not invent observed measurements. Owner-scoped runs preserve decisions, failures, events and evidence, with timeout, iteration, token and shared spending controls.

A new hosted judge-account execution on October 29 completed six real model selections and six scientific tools with six artifacts and no recovery. Its accepted plan was generated deterministically, so this is evidence of real model-guided execution, not a claim of a newly model-generated plan. A preceding partial attempt and earlier generic-model/direct-Meta results retain their actual identities and failure records.

## Why are Meta models important to your solution

Meta models connect a researcher's natural-language objective to explicit analysis decisions informed by previously computed evidence. They provide a flexible interface for choosing among permitted scientific tools while keeping numerical work reproducible and inspectable.

The central capability is the traceable link between a model proposal and its verified tool output. NeuroLab AI exposes that link through saved decisions, evidence reports and execution visualizations. Meta Muse Spark Open provides an open-weight model option through a hosted partner. Independent human review of the separate comparison is still pending, so I do not claim superior answer quality or a winning agent policy.

## Feedback on Meta products

Structured model actions made an inspectable research workflow possible, but successful inference alone did not guarantee completion. The initial audited investigation failed its objective. I retained the failures, improved orchestration and evidence handling, and reran the original investigation with real model decisions and reproducible tools under a documented larger execution budget.

Strict response validation remains necessary. During the October 29 hosted hackathon-model check, one response failed schema validation; the application rejected it, recorded the failure and labelled recovery. That attempt remained PARTIAL. A separately recorded second attempt completed without recovery. Clearer availability diagnostics and consistent model and credential instructions would improve the developer experience. The prototype's records expose these limitations rather than treating every successful API call as a scientific result.

## Feedback on partner technologies

Baseten's OpenAI-compatible API and named function calling enabled hosted Meta execution from Render. The initial generic model integration worked, but the hackathon-specific identifier returned 404 when used with the regular account key. After locating and configuring the separately emailed hackathon key, the exact meta-models/muse-spark-open-1026 identifier returned HTTP 200 and subsequently completed a hosted six-tool investigation.

The missing distinction was the separate hackathon credential, rather than the availability of regular account credits. Making that distinction prominent in onboarding would save debugging time. Baseten's email confirmed a $100 hackathon credit award and up to 2M tokens per minute. I have not used Fireworks or Modal in the verified executions described here.

## Live application

https://neurolab-ai.vercel.app

## Private judge access notes

Provide the prepared judge email/password and instructions through the portal's private access field. Do not put credentials in public descriptions, the repository or video. Judges should open Experiment Studio, choose Full Ghana investigation, then explicitly select Meta-assisted research before starting. The preset initially selects deterministic mode. The latest saved exact-model run is 133339f4-bc9c-472e-bd1c-deaa188d9a4a. Application budgets and provider availability can limit new runs.

## Publication permission

Read the form's consent statement and accept it yourself only if you agree. This document does not grant permission or submit the form.

## Final review

Check the public video URL and signed-out playback, privately deliver judge access, confirm eligibility and contribution timing, and retain scientific caveats. The verified project start is October 26; some work predates the listed kickoff and the guide separately lists building from October 27. Do not alter history or treat hosted success as organizer approval. Human comparison review remains deferred. Nothing has been submitted by this update.
