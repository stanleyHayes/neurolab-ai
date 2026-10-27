# NeuroLab AI demo recording guide

Prepared 27 October 2026

This guide takes you from preparing a research question to recording an honest demonstration of NeuroLab’s analysis, evidence, follow-up investigations and stopping decisions. Use the three-minute script for the submission cut and the operating instructions to rehearse the complete workflow.

**The recording mode is deterministic analysis on real Ghana trial data.** Meta inference stays paused because credits are exhausted. “Simulation” here means an offline research workflow or replay of saved processing; it does not mean simulated crop measurements, a crop-growth model or a new live AI call.

## 1 Choose the story before recording

Your central question is: **Which maize genotypes deserve further drought research, and what evidence or uncertainty supports that shortlist?**

A successful demo ends with an auditable exploratory shortlist or an explicit explanation of why the evidence is insufficient. It does not have to identify a proven drought-resilient variety. An inconclusive result can be the right scientific outcome.

Show one complete investigation, one evidence-driven follow-up and a clear decision to stop or propose new field work. Keep additional follow-ups available for a longer walkthrough rather than squeezing every screen into three minutes.

The repository’s earlier three-minute storyboard assumes live Meta planning and suggests an evaluation comparison. This guide supersedes those assumptions for this recording. Do not narrate live Meta reasoning, policy superiority, production readiness or new discoveries that the demonstrated evidence does not establish.

## 2 Prepare the recording session

### Before opening the recorder

1. Use your working local application and an authorized account. Sign in before recording so no password, invite token or personal account details appear.
2. Confirm the frontend, API, database and research worker are running. A healthy webpage alone does not prove that a worker can consume queued investigations. Rehearse one small Dataset profile run and verify it reaches a terminal state.
3. Keep `MODEL_INFERENCE_ENABLED=false`. The interface should show Meta-assisted research as paused. Choose **Deterministic analysis**. Do not enable a provider simply to make the demo look more advanced.
4. Open the source provenance panel. Confirm the loaded source has 864 plots and 72 genotypes, with 432 observations in each water regime. Treat the three ENVT codes as trial-environment indices, not calendar years.
5. Prepare one completed, owned full investigation as fallback footage. Open its report, inspect its six numeric artifacts and check that its source fingerprint matches the current dataset. Do not use an unowned historical record or assume an old run is complete from its title.
6. Export that run’s evidence before recording. Keep the original download unchanged. Note the run ID, seed, source hash and report status in your rehearsal notes.
7. Put the objectives in section 4 into a separate text window for quick copying. Keep that window outside the captured region.
8. Close email, dashboards, terminal windows and unrelated browser tabs. Disable notifications and hide the bookmarks bar if it exposes personal information.

### If the local application is not already running

Skip this section when your working demo is already open. For an existing, configured checkout, start the API, worker and frontend in three separate terminals from the project directory. Keep the API and worker pointed at the same database. These commands assume dependencies, the database, authentication and the private `.env` are already configured as described in README; they do not provision a new installation.

API terminal:

```sh
source .venv/bin/activate
set -a
source .env
set +a
export MODEL_INFERENCE_ENABLED=false
export RESEARCH_INLINE_WORKER=false
uvicorn neurolab.api:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Worker terminal:

```sh
source .venv/bin/activate
set -a
source .env
set +a
export MODEL_INFERENCE_ENABLED=false
python -m neurolab.worker
```

Frontend terminal:

```sh
npm run dev
```

Open `http://localhost:3000` and sign in. If you use an already configured review environment on other ports, keep its matching frontend, API and database instead of mixing environments. Do not display these environment-loading terminals in the recording.

### Frame and sound

Record a 1920 × 1080 landscape window when available. Make text readable at the final video size; start around 100–110% browser zoom and adjust after a test capture. Use a microphone in a quiet room. Record ten seconds, play it back and check the voice, chart labels and cursor visibility.

On this Mac, Shift–Command–5 opens the built-in screen recorder. Select the app window area and choose your microphone in Options. A recorder you already use is equally suitable. Face camera is optional unless the program requires it. No music is needed.

The repo targets a submission video of no more than three minutes. Aim for about 2:50 to leave room for a title and clean ending. Recheck the organizer’s current duration, file, hosting and eligibility rules before submission; this document does not verify the live program rules.

### Record in separate takes

Capture the introduction, setup, processing, results, follow-up and closing separately. Leave two seconds of stillness before and after each take. You can then remove typing and waiting without rushing the explanation. If you shorten execution time, add **“Processing shortened”**. If you show saved processing, add **“Replay of a previously completed deterministic run”**. Keep the actual run identity consistent across the result and evidence shots.

## 3 Prepare the main investigation

1. Open the experiment setup screen and paste the main objective below. For the full original maize brief, copy the exact text from `tests/fixtures/ghana-research-objective.txt` instead; the preset keeps your wording.
2. Click **Full Ghana investigation**. This selects the canonical Ghana dataset, all six methods, four declared exploratory criteria, the report outputs and deterministic mode.
3. Open **Optional research configuration** briefly. Confirm six analysis steps, six tool calls and 180 seconds. Keep seed 2026. This is a configured limit, not a claim that execution takes 180 seconds.
4. Confirm **Deterministic analysis** is selected. Do not use Meta refinement for this recording. If an accepted plan from an earlier objective is present, reject or clear that proposal before preparing the new objective; an accepted plan can take precedence over method selection.
5. Click **Start investigation** once. Show the persisted processing timeline. A queued state means accepted for execution, not completed science.
6. When the run finishes, check its status and completed artifacts. A failed, cancelled, timed-out or partial run must retain that label. For the intended complete demonstration, verify all six methods executed rather than relying only on a completion badge.
7. Open the results and Reports views for that same run. Show the source identity, one result, one uncertainty statement, candidate trade-offs and the evidence export.

Do not promise arbitrary file uploads, IITA pooling, new irrigation treatments or simulated future harvests. The current supported analysis path is the existing canonical Ghana combined dataset. Its component files duplicate these plots and cannot increase the sample size.

## 4 Copy and paste objectives

### Main run

**Working title:** Ghana drought candidate investigation

> Using the Ghana combined maize trial dataset, identify exploratory candidates for follow-up drought research. Audit source provenance and missing values, compare observed grain yield between water regimes, summarize genotype drought means and descriptive yield retention, examine genotype-mean trait associations, and assess sensitivity across observed environments. Report uncertainty, counter-evidence and limitations. Treat ENVT codes as environment indices rather than years, do not pool overlapping source files, and distinguish a proposed future field trial from work actually executed.

Use **Full Ghana investigation** for this objective. Its four fixed criteria cover observed top-quartile consistency, ASI association, numeric STYG association and omitted-environment rank movement. They are declared retrospective rules, not independently preregistered hypotheses. Additional questions can remain unassessed even when the six-method workflow finishes.

### How to configure a focused follow-up

Return to setup. Under Desired outputs, deselect **ghana drought investigation**; otherwise the full six-method contract still applies. Clear the previous preferred methods and any accepted plan, then select exactly the method or methods listed below. Retain **research report** and the relevant output. Use deterministic mode, seed 2026, and the stated budgets. Give each run a distinct working title.

These follow-ups analyze the same observed dataset. They do not collect new independent evidence, automatically inherit a previous run’s candidate selection or create a validated combined score. Naming a genotype in the objective does not guarantee a genotype filter; use the returned panel and inspect the matching row manually.

### Follow up A Check whether the shortlist depends on environment

**Title:** Ghana environment sensitivity follow up  
**Methods:** Environment sensitivity; Genotype summaries  
**Outputs:** research report; environment summaries; genotype summaries  
**Budget:** 2 steps; 2 calls; 60 seconds

> Assess observed drought-yield variation and leave-one-environment-out rank sensitivity in the Ghana combined dataset. Compare the leading descriptive genotype means with their observed environment profiles and rank changes. Explain whether the initial shortlist depends strongly on a particular environment. Do not describe these checks as validated future stability or prediction.

**Why run it:** A large overall mean can hide uneven observed performance. Compare the leading rows with the previous run’s shortlist; record both favorable evidence and rank movement. The full investigation already includes this method, so this focused run demonstrates a narrower workflow and reproducibility, not a new discovery.

### Follow up B Check a possible trait explanation

**Title:** Ghana drought trait association follow up  
**Method:** Trait associations  
**Outputs:** research report; trait associations  
**Budget:** 1 step; 1 call; 60 seconds

> Examine observed genotype-mean associations between drought grain yield and the available traits, including ASI and numeric STYG. Report correlation directions, conditional resampling intervals and consistency across the recorded environments. Keep score-direction uncertainty and multiple-screening limitations visible. Do not infer causation or claim a validated predictor.

**Why run it:** This investigates whether a proposed explanation is compatible with the observed panel. An interval crossing zero or inconsistent directions is a reason for caution. Numeric STYG direction is not verified, so do not translate a negative coefficient into a biological claim about greener plants.

### Follow up C Resolve a data quality concern

**Title:** Ghana source and missingness check  
**Methods:** Dataset profile; Missingness audit  
**Outputs:** research report; missingness summary; provenance export  
**Budget:** 2 steps; 2 calls; 60 seconds

> Audit the Ghana combined source, record counts, water-regime coverage and missing analytic values. Identify limitations that affect yield comparisons and genotype summaries. Explain why the combined file and regime-specific component files cannot be pooled as independent observations, and why ENVT codes cannot automatically be treated as calendar years.

**Why run it:** Use this when a result is unavailable, sample coverage differs or an interpretation depends on missing fields. Missing values must remain missing; do not change source measurements to make a hypothesis pass.

## 5 Interpret the results on screen

Read every result in this order: **what was computed → which records contributed → uncertainty → limitation → next decision**.

- **Regime contrast:** Describe observed means and their difference in kg/ha. Retention is drought mean divided by a positive well-watered mean, multiplied by 100. It is a descriptive ratio, not the causal effect of irrigation. Water regime is confounded with trial environment.
- **Bootstrap interval:** Read the endpoints and method from the selected run. It is a conditional block-bootstrap interval under the implemented sampling scheme. It does not correct every design limitation or prove causation.
- **Genotype summaries:** Say “largest observed drought means” or “candidates for follow-up.” Inspect coverage, retention and environment sensitivity together. Rank confidence, alpha-lattice adjustment and validated future performance are not established by the descriptive ranking.
- **Environment sensitivity:** Omitted-environment ranks show how the observed summary changes when an environment is left out. Their range is not a confidence interval, and three observed environments do not establish broad adaptation.
- **Trait associations:** Correlation is a panel-level association, not a mechanism or proof that changing a trait increases yield. Conditional intervals and repeated trait screening need caution.
- **Hypothesis assessments:** “Observed criterion met” means the declared rule was met in these data. “Not met,” “Inconclusive” and “Not assessed” are different outcomes. None should be rewritten as a successful scientific validation.

### Rehearsal reference from saved evidence

The preserved run `971d3426-4768-4784-bb0d-a665bdb0b007` reports drought and well-watered means of approximately **1,230.3 and 2,616.0 kg/ha**, an observed difference of **−1,385.8 kg/ha**, descriptive retention of **47.0%**, and a conditional 95% block-bootstrap difference interval of approximately **−1,552.2 to −1,215.7 kg/ha** with seed 2026.

In that saved run, **TZm-1179** has an observed drought mean of approximately **2,370.3 kg/ha** and meets the observed top-quartile criterion in each recorded drought environment. This supports discussing a follow-up candidate; it does not prove a deployable drought-resilient variety.

These are reference values from `verification/maize-investigation/figure-data.json`, not numbers to force into a new recording. Read the selected run’s actual values. If they differ, check the source hash, method, configuration and run identity before explaining why. Never paste reference values into the interface or claim this historical run was just executed.

## 6 Three minute spoken script and screen actions

Read naturally and pause on the evidence. The timings are editing targets, not measured execution times.

### 0:00 to 0:20 Introduce the problem

**Show:** Workspace, then source provenance.

**Say:**

> “I built NeuroLab AI to help researchers turn maize trial records into traceable evidence. Today I’m asking which genotypes deserve further drought research. This demonstration uses real Ghana data in deterministic mode. Meta inference is paused, and the numeric results come from scientific tools.”

### 0:20 to 0:45 Prepare the question

**Show:** 864 plots, 72 genotypes, source citation; paste the objective and select Full Ghana investigation.

**Say:**

> “The source contains 864 plots and 72 genotypes. I keep the original research objective and select the full investigation: provenance, missingness, regime comparison, genotype summaries, trait associations and environment sensitivity. The analysis has a fixed seed and bounded execution.”

### 0:45 to 1:05 Start and show processing

**Show:** Click Start investigation; show actual timeline and Open cinematic view. If the run finishes too quickly, use the saved replay and its label.

**Say for actual execution:**

> “I start the investigation here. The timeline records tool execution and saved evidence. The cinematic view presents those records; the maize illustration is not measured plant geometry. This run makes no model call.”

**Alternative for saved processing:**

> “This is a replay of a previously completed deterministic investigation. The timeline presents saved tool events and results. It does not rerun an AI model, and the maize illustration is not measured plant geometry.”

### 1:05 to 1:40 Read the evidence

**Show:** Regime contrast with uncertainty; candidate trade-offs; one criterion and its evidence.

**Say:**

> “The observed drought mean is lower than the well-watered mean. I read the difference alongside its conditional bootstrap interval. Because water regime is confounded with environment, this is not a causal irrigation effect. I then inspect candidate means, coverage, retention and rank sensitivity. A high mean identifies a research lead, not a proven variety.”

### 1:40 to 2:15 Ask the next question

**Show:** Follow-up A objective and two selected methods; start it; show its actual environment result. Shorten waiting with a label if needed.

**Say:**

> “My next question is whether the shortlist depends on one environment. I switch to a focused investigation and examine observed environment profiles and omitted-environment ranks. This is another analysis of the same records, not new independent evidence. If the shortlist changes substantially, I keep that uncertainty rather than hiding it.”

### 2:15 to 2:40 Show reproducibility

**Show:** Reports, source fingerprint, run ID and Export evidence & figures data.

**Say:**

> “The report preserves the criteria, findings, counter-evidence and unresolved questions. I can export the report, numeric artifacts and recorded events. The source fingerprint and execution metadata let another researcher trace which data and methods produced the result.”

### 2:40 to 2:55 Explain the stopping decision

**Show:** Limitations and proposed next experiment in the report.

**Say:**

> “I stop when the supported questions are answered or the data cannot resolve them. Here, the next step is independent field validation. NeuroLab helps me make that decision with an auditable trail, while keeping exploratory evidence separate from a field recommendation.”

Leave the final five seconds for a still report screen. Do not show a public product or code link unless you have checked it works without privileged access.

## 7 Decide whether to continue or stop

Decide what counts as adequate evidence before inspecting candidate names. For this demo, use the app’s declared observational criteria and report counter-evidence; do not invent a favorable numerical threshold after seeing results.

| What you observe | What to do next | What to say |
|---|---|---|
| Large means with uncertain environment consistency | Inspect existing sensitivity evidence or run follow-up A | “The mean alone is insufficient; I’m checking dependence on observed environments.” |
| A proposed trait explanation needs checking | Inspect the trait report or run follow-up B | “I’m testing compatibility with the observed association pattern, not a causal mechanism.” |
| Missing values, unequal coverage or unavailable output | Run follow-up C and inspect exclusions | “I need to understand coverage before interpreting this estimate.” |
| The supported checks converge on a reasonable shortlist | Export the evidence and propose independent validation | “These are exploratory candidates for a new field trial.” |
| Contradictory directions, unstable ranks or inconclusive criteria remain | Preserve the disagreement and stop the claim | “These records do not justify a stronger conclusion.” |
| The question needs future yield, causal water effects, IITA matching or unsupported modeling | Stop this computational workflow and document the requirement | “This requires additional data or a method that is not supported here.” |
| Execution is partial or has failed | Inspect pending tasks/error; correct the operational cause before a new run | “This run did not complete the intended analysis.” |

Rewording the same question or repeating a deterministic run does not add evidence. Changing the seed until a result looks favorable is not an acceptable research strategy. Keep unsuccessful and inconclusive runs in your notes. If you change the question after seeing results, call the follow-up exploratory and record the reason.

For each follow-up, write down: parent run ID; observation that triggered it; new objective; selected methods; limits and seed; new run ID; result; contradiction; and stop/continue decision. This notebook link is manual unless the application explicitly records a relationship; do not claim automatic cross-run reasoning.

## 8 Demonstrate cancellation and handle problems

Cancellation is optional in the short cut. For a longer recording, click **Request cancellation** only while a run is active, then show the acknowledged terminal state. A tool already running may finish before the worker observes cancellation. Do not call a cancellation request an immediate process kill. Fast runs can finish before you click; never manufacture a cancellation result.

If a run remains queued, check the worker instead of repeatedly submitting. If a request is throttled, respect the retry delay. If a run times out, inspect which tasks completed before choosing a bounded follow-up. A partial report can be audited but cannot stand in for a complete six-method investigation.

If the cinematic 3D view stutters, select **Standard 2D** and continue with the same evidence. The visualization is presentation, not a calibrated crop simulator. If the source is unavailable or its hash differs, stop the new analysis; use a clearly identified saved run only if its evidence is intact.

If execution fails during recording, retain the failed take in your working footage. Switch to the rehearsed saved run and say: **“I’m switching to a previously completed run to show its saved evidence.”** Do not edit the footage to imply that the failed run produced the saved result.

## 9 Finish the recording and submission cut

Watch the exported video from beginning to end at its actual playback size. Check that the viewer can read one objective, one measured result, uncertainty, a follow-up and a stopping decision. Confirm voice volume, accurate run labels, no exposed secrets, no invented model activity and a duration within the current program limit.

Keep the screen recording, voice track, evidence download and final video together. If you upload a public video, test the exact link from a signed-out browser and save the submission receipt. Publication and submission remain your final delivery steps; this guide does not assert they have happened.

### Rehearsal checklist

- [ ] Authorized account signed in and private information hidden.
- [ ] Meta paused and deterministic mode visible.
- [ ] Source citation, 864 plots, 72 genotypes and overlap caveat checked.
- [ ] Main objective preserved; six methods and 6/6/180 limits confirmed.
- [ ] Actual six-tool completion and report inspected.
- [ ] One focused follow-up configured without the full-profile output or stale accepted plan.
- [ ] Candidate conclusion, uncertainty and stopping statement rehearsed.
- [ ] Saved-run fallback and original evidence export prepared.
- [ ] Processing cuts and saved replays labeled accurately.
- [ ] Final duration, audio, legibility and current organizer rules checked.

## Repository references

This guide follows the current UI source and the authoritative methods documents: `README.md`, `Architecture.md`, `docs/DETERMINISTIC_INVESTIGATION_PROFILE.md`, `docs/FOCUSED_REPLAY_ROUTING.md`, `docs/OBSERVATIONAL_SENSITIVITY_METHODS.md`, `docs/SCIENTIFIC_REPORT_EXPORT.md` and the saved evidence in `verification/maize-investigation/`. The original objective is preserved in `tests/fixtures/ghana-research-objective.txt`.
