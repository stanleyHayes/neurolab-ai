# NeuroLab AI submission form answers

Prepared for Stanley Hayford on 28 October 2026. Copy the answer beneath each field into the submission form. Review the final checklist before submitting; the video URL is still outstanding.

## Team Name

NeuroLab AI

## Team Members

Stanley Hayford — sahayford

Solo entrant. Keep the single member shown in the form unless another actual contributor needs to be disclosed.

## Which track are you submitting to

Indie Developer Track

## Which problem statement did you build towards

Push the Frontier

Recommended selection: the project explores verifiable scientific agent workflows using real agricultural data, bounded model decisions and reproducible numerical tools.

## Most Viral Track X post link

Leave blank unless you choose to enter this optional award and have published a qualifying X post. No post URL has been supplied.

## Project Description

NeuroLab AI is a scientific research prototype that helps researchers investigate drought-related patterns in published Ghana maize trial data. It turns a research objective into a reviewable analysis plan, uses Meta models to propose structured tool actions, and executes those actions through validated Python tools. Researchers can inspect genotype rankings, environment sensitivity, water-regime comparisons and trait associations, then use the evidence to choose a follow-up analysis or stop when the available data cannot support a stronger conclusion.

The prototype addresses a practical problem: a convincing AI explanation can be difficult to distinguish from an analysis grounded in measurements. NeuroLab AI preserves source lineage, model decisions, computed artifacts and scientific limitations in saved runs and exportable reports. Its charts and cinematic execution view reflect recorded tool events and results. Explicitly labelled deterministic replay keeps the workflow usable without paid inference.

A real Baseten-hosted Meta Muse Spark Open execution completed the original exploratory investigation with six model selections and six scientific tools, producing six result artifacts without deterministic recovery. The application combines a Next.js interface on Vercel with a FastAPI service, standalone worker and PostgreSQL on Render. Its current dataset contains 864 plot records covering 72 maize genotypes. Results are exploratory: water regimes are confounded with trial environments, and the application does not provide validated field recommendations.

## Public GitHub Repository

https://github.com/stanleyHayes/neurolab-ai

## 3 Minute Demo Video

REQUIRED BEFORE SUBMISSION — insert the publicly accessible URL of the final reviewed demo video.

The latest American-voice local video, NeuroLab-American-Demo.mp4, is 2 minutes 59.20 seconds and includes verified start-date/code-contribution disclosure, actual research footage, exact model labels and generated narration/subtitles. Listen through it before publishing, then check signed-out playback. A local file path is not a submission URL.

## Describe your use of Meta products to build the submitted project

NeuroLab AI uses Meta models as the decision-making component of a bounded research agent. The direct Meta Model API integration has recorded real Muse Spark 1.3 executions, including an investigation of the original research objective and a separate evaluation containing 72 real-model trials. A second integration serves Meta Muse Spark Open through Baseten's OpenAI-compatible API. In the recorded hosted investigation, that model selected six analyses and the scientific tools produced six persisted artifacts.

Model proposals are constrained to structured JSON actions and validated on the server against schemas and an allowlist. With Baseten, the adapter requests a single named function call and validates its arguments before dispatch. Python tools compute the numerical findings; the model does not supply observed measurements. Each run preserves provider and model identity, decisions, tool outputs and failures, with iteration, timeout, token and spending controls.

The recorded hosted scientific investigation used meta-models/muse-spark-open. On October 29, after configuring the separate hackathon key supplied by email, a real request to the required meta-models/muse-spark-open-1026 returned HTTP 200 and a schema-validated function response. Earlier 404 attempts used the regular account credential. Exact hackathon-model connectivity is now verified; the earlier six-tool investigation is not relabelled as a six-tool run on the hackathon identifier.

## Why are Meta models important to your solution

Meta models connect a researcher's natural-language objective to a sequence of explicit analysis decisions. They can propose the next permitted tool action in the context of the objective, the accepted plan and previously computed evidence. This makes the interaction more flexible than a fixed sequence of dashboard queries while keeping the numerical work reproducible and inspectable.

The important capability is a traceable link between a model's proposal and a tool's measured output. NeuroLab AI makes that link visible through saved decisions, evidence reports and execution visualizations. Meta Muse Spark Open also provides an open-weight model option through a hosted partner, while the direct Meta integration supplies a separate recorded execution path. The project has not yet established superior scientific answer quality: independent human review of the comparison remains pending.

## Provide feedback from your experience using Meta products

Structured model actions made it possible to build an inspectable research workflow, but successful inference alone was not sufficient for scientific completion. The initial audited investigation failed to meet its objective. The engineering work addressed orchestration and evidence handling, retained the failed attempts, and reran the original objective and accepted plan with real model decisions and reproducible tools. Completion required an explicitly documented increase in the execution budget; it is not claimed as success under the original smaller budget.

Clear provider/model identity, response validation, preserved tool feedback and honest scientific scope were essential to diagnosing failures. The direct Meta endpoint returned HTTP 404 from the hosted Render environment even though separate local executions succeeded; its underlying cause remains unconfirmed. The Baseten integration subsequently completed the hosted investigation using Meta Muse Spark Open. More precise model-availability diagnostics and consistent identifiers across participant guides, account catalogs and deployment documentation would make integration and event verification easier.

## Provide feedback from your experience using partner technologies

Baseten's OpenAI-compatible API enabled real hosted Meta Muse Spark Open execution from the Render backend. The documented meta-models/muse-spark-open identifier returned successful responses, including a streaming test and a complete six-tool scientific investigation. Named function calling provided the structured action interface needed by the agent, with server-side validation retained.

The main integration challenge was distinguishing the regular account key from the separately emailed hackathon key. The guide-specific meta-models/muse-spark-open-1026 identifier returned 404 with the regular key, then succeeded with HTTP 200 and a validated function response after the emailed hackathon key was configured on October 29. Making that credential distinction more prominent in onboarding would help. I have not used Fireworks or Modal in the verified execution described here. Baseten's email confirmed a $100 hackathon credit award and up to 2M tokens per minute.

## Permission to use and promote submitted materials

Review the form's permission statement personally before checking the box. It grants Meta and Cerebral Valley permission to use, publish, share and promote the submitted materials. This preparation document does not accept that permission or submit the form on your behalf.

## Final checks before submission

- Replace the video reminder with the final public video URL and test signed-out playback.
- Confirm your eligibility for the Indie Developer Track and the accuracy of the single-member listing.
- Include an accurate account of new work, the earlier prototype, source data and reused assets in the final demo. Use the contribution disclosure linked below; commit dates alone do not prove eligibility.
- Confirm the guide-specific Baseten model requirement with the organizer or provider. Update the model-access statements only after new evidence; do not silently relabel the successful generic-model run.
- Verify that the repository is public and that the live app is reachable. Arrange judge access privately if required; never publish keys, passwords or universal access credentials.
- Keep the scientific caveats. Do not claim field validation, superior model quality or completed independent review.
- Review publication permission, then submit the final form yourself.

## Supporting information

Live application: https://neurolab-ai.vercel.app

Current source license: MIT; preserve separate dataset and third-party asset attribution.

The documented deadline is 4 November 2026 at 21:00 EST, equivalent to 5 November at 02:00 in Accra. Confirm the portal's final displayed deadline before submission.

Internal project references:

- [Event alignment](EVENT_ALIGNMENT_2026_10_28.md)
- [Contribution disclosure](EVENT_CONTRIBUTIONS_2026_10_28.md)
- [Video revision brief](demo/video/EVENT_REVISION_BRIEF.md)
- [Successful hosted investigation evidence](../verification/baseten-activation-2026-10-28/original-proof.json)
- [Separate failed event-alias request](../verification/event-readiness-2026-10-28/required-model-probe.json)
