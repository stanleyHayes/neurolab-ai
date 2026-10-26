# NeuroLab AI

**Reproducible, evidence-linked analysis of African maize field trials.** NeuroLab AI is a research prototype that brings real trial data, deterministic scientific tools, and bounded AI-assisted workflows into one research workspace.

> **Status:** Working research prototype; not a production agronomy service. The current analysis MVP uses the Ghana maize dataset. A real Meta Model API adapter has been smoke-tested, but an audited end-to-end agent run did **not** meet its target research objective. Results are exploratory and must not be used as field recommendations.

**Repository:** [github.com/stanleyHayes/neurolab-ai](https://github.com/stanleyHayes/neurolab-ai) · **Current publication status:** project description and README are published; the application source tree is not yet present in the public repository.

---

## What it does

NeuroLab is designed for agricultural researchers, plant breeders, and students exploring questions about maize performance under contrasting trial conditions. Its current workspace provides:

- **Real-data exploration** of the Ghana maize trial records, including dataset profile and missingness.
- **Reproducible analyses** for exploratory regime contrasts and descriptive genotype rankings, computed by deterministic server-side tools.
- **Evidence-linked research runs** with persisted events, analysis artifacts, source lineage, and report/export views.
- **Bounded AI assistance** through an optional, schema-constrained provider adapter. The model can request only allowlisted actions; validated tools compute the numeric results.
- **A responsive Next.js research workspace** for experiments, results, data provenance, reports, and saved-run replay.
- **Deterministic replay mode** so core development and evaluation can run without paid model access. Replay is not an AI call.

NeuroLab studies existing computational trial records. It does not run a real-world irrigation experiment, perform wet-lab work, or include a calibrated crop simulator.

## Scientific and safety boundaries

- Treat outputs as **descriptive or exploratory evidence**, not causal effects, validated predictions, or agronomic recommendations.
- The Ghana source includes 864 combined plot records across drought and well-watered regimes, 72 genotypes, and three trial-environment codes. Water regime and environment are confounded; comparisons do not isolate a causal irrigation effect.
- Genotype rankings are descriptive. Current ranking does not model alpha-lattice effects, adjust for multiple comparisons, or estimate ranking uncertainty; it is not a stability analysis.
- Environment codes are not automatically calendar years. Preserve the source metadata when interpreting them.
- The combined Ghana source duplicates its two regime-specific files. Do not concatenate the combined file with its components as if they were independent observations.
- IITA data are included in the raw-data audit/staging pack, but are **not enabled as analysis-ready datasets** in the service. Do not join IITA trials by row order or genotype identifier alone.
- The model proposes bounded actions or summarizes verified tool outputs; model-generated narrative is not itself a scientific result. A successful provider smoke test is not evidence that the agent answers research questions reliably.

## Architecture

```text
Browser
└── Next.js App Router · React · TypeScript
    └── same-origin /api proxy
        └── FastAPI · Pydantic · JSON-schema validation
            ├── Immutable source CSVs → normalized Ghana records
            ├── Deterministic profile / contrast / ranking / missingness tools
            ├── Optional bounded Meta-compatible structured-output adapter
            └── PostgreSQL run, event, and artifact persistence
```

The API is the authority for tool validation, execution, persisted events, and research artifacts. SQLite is supported for isolated tests; the documented default service database is PostgreSQL. The model path is optional, uses server-side credentials, and is subject to provider access, quotas, and costs.

## Current implementation status

The repository’s verification records (2026-10-26) document a passing local quality gate, source-data integrity checks, Ghana normalization, and HTTP 200 smoke responses for all 12 workspace routes. The mobile navigation drawer has been implemented, but full browser-based keyboard, focus, and interaction acceptance remains outstanding.

The live Meta `muse-spark-1.3` adapter was smoke-tested, and a bounded run executed real tools on the Ghana source. That run was **partial and failed its requested research objective**: it profiled the data, inspected missingness, then recovered from an invalid action by repeating the profile. It did not produce genotype stability analysis or a justified next experiment. See [`verification/AGENT_EXECUTION_TRACE.md`](verification/AGENT_EXECUTION_TRACE.md), [`verification/UI_ACCEPTANCE.md`](verification/UI_ACCEPTANCE.md), and [`verification/DEFECT_REGISTER.md`](verification/DEFECT_REGISTER.md) for evidence and remaining blockers.

**This is not production-launch-ready.** There is no end-user authentication or per-user data isolation, distributed durable job queue, shared/global rate limiting, verified deployment, or backup/restore process. Browser interaction and accessibility acceptance is incomplete. Do not expose the service as a public multi-user application.

## Getting started (full source checkout)

> The public GitHub repository currently contains this README and repository metadata only, not the application source files. The following commands work after the complete project source tree and its `data/`, `neurolab/`, `scripts/`, and `app/` directories are available locally.

### Prerequisites

- Python 3.12
- Node.js 20.19 or newer and npm
- PostgreSQL for the service’s default local configuration
- macOS/Linux shell for the commands below (adapt virtual-environment activation for Windows)

### Install dependencies

From the full project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
```

For a local PostgreSQL setup, create the development database before starting the API:

```bash
createdb neurolab
```

Copy `.env.example` to `.env` and configure values as needed. The Python API does not automatically load `.env`; export its values in the API shell before startup. Keep `.env`, model credentials, and production secrets out of source control.

### Audit and prepare data

```bash
python scripts/audit_datasets.py
python scripts/normalize_ghana.py
```

The audit validates source row counts, columns, fully empty rows, and SHA-256 checksums against `data/manifest.json`. Normalization writes derived outputs to the ignored `data/processed/` directory; source CSVs are immutable.

### Run the API and dashboard

Start the API in one terminal:

```bash
source .venv/bin/activate
set -a; source .env; set +a
uvicorn neurolab.api:app --reload --port 8000
```

Start the Next.js app in a second terminal:

```bash
npm run dev
```

Open <http://localhost:3000> for the workspace. In development, FastAPI OpenAPI docs are at <http://127.0.0.1:8000/docs>. Set `RESEARCH_API_URL` if FastAPI is not listening at `http://127.0.0.1:8000`.

### Optional Meta provider

Replay mode requires no provider credential. Live provider mode is optional and may incur provider charges. Configure the server-side variables documented in `.env.example` (`META_MODEL_API_KEY`, provider/model settings, budgets, and verification flag). Set `META_MODEL_VERIFIED=true` only after successfully running the provider smoke check with your own credentials:

```bash
set -a; source .env; set +a
python scripts/smoke_meta_provider.py
```

Never put provider credentials in browser code, `NEXT_PUBLIC_*` variables, source control, screenshots, or logs. Provider availability, quotas, and pricing are controlled by the provider. Live integration verification does not constitute scientific or answer-quality validation.

## Quality and evaluation

Run the project quality gate from the full source root:

```bash
make quality
```

It runs Python lint/format checks, frontend lint and TypeScript checks, Python tests, dataset integrity validation, Python compilation, and a production Next.js build. Individual checks can also be run with:

```bash
python -m unittest discover -s tests -v
npm run lint
npm run typecheck
npm run build
```

The deterministic workflow-coverage fixture can be reproduced with:

```bash
python scripts/run_evaluation.py --seed 77 --budget 2
```

This fixture evaluates tool-selection coverage on a fixed task catalog. It does **not** score scientific-answer quality, model groundedness, human-rated utility, or live Meta performance; do not present it as such.

## Data provenance

- **Ghana maize trial data:** Abu et al. (2026), *Phenotypic data: drought-tolerance evaluation of early and extra-early African maize (Zea mays L.) landraces*, [Zenodo DOI 10.5281/zenodo.22666201](https://doi.org/10.5281/zenodo.22666201), CC BY 4.0. The 864-row combined CSV is the active analysis source; regime component files are retained for cross-checking and must not be counted again.
- **IITA trial data:** Menkir et al., *Regional trials of Striga resistant and drought tolerant maize hybrids conducted for eight years*, [DOI 10.25502/4xv7-bc93/d](https://doi.org/10.25502/4xv7-bc93/d), listed as CC BY 4.0 on its dataset landing page. These files are audited/staged, not enabled in the current analysis API. The full-irrigation CSV contains substantial fully empty rows, which are recorded in the audit documentation.

Raw-file inventory, checksums, data handling, and detailed license notes are documented in [`docs/01_Data_Inventory_and_Provenance.md`](docs/01_Data_Inventory_and_Provenance.md) and `data/manifest.json`. NASA POWER, FAO AquaCrop, and CIRAD AgMIP are not bundled. Confirm source terms and permissions independently before reuse, especially for commercial use or adding sources beyond those listed here.

## Documentation

- [`Architecture.md`](Architecture.md) — service boundaries and data flow
- [`Agent_plan.md`](Agent_plan.md) — implementation and release gates
- [`BUILD_LOG.md`](BUILD_LOG.md) — dated changes and validation evidence
- [`verification/IMPLEMENTATION_AUDIT.md`](verification/IMPLEMENTATION_AUDIT.md) — implementation scope and audit findings
- [`verification/SCIENTIFIC_VALIDATION.md`](verification/SCIENTIFIC_VALIDATION.md) — independent arithmetic and source checks
- [`verification/AGENT_EXECUTION_TRACE.md`](verification/AGENT_EXECUTION_TRACE.md) — actual bounded provider execution and its limitations
- [`verification/DEFECT_REGISTER.md`](verification/DEFECT_REGISTER.md) — known defects and launch blockers

## Contributing and responsible use

Contributions should preserve source files, provenance, deterministic reproducibility, schema validation, and honest uncertainty. Add tests for behavior changes, report only checks actually run, and append material project work and evidence to `BUILD_LOG.md`. Do not commit secrets, private data, generated database files, or restricted assets. Before opening the service to additional users, implement user authentication and authorization, per-user run isolation, shared abuse/cost controls, durable jobs, deployment and recovery procedures, and complete browser/accessibility acceptance.

The current workspace has no `LICENSE` file. Dataset licenses do not automatically license application code; no open-source license for the project code is implied by this README.