# Local judge walkthrough without hosted accounts

This path runs the real published Ghana dataset and scientific tools on your computer. It does not require the entrant's hosted account, an API key, model credits or any cloud login. It is explicitly deterministic analysis, not a new Meta call or a calibrated crop simulator. Internet access is needed to clone and install dependencies; the walkthrough then uses local services and data.

## Prerequisites and installation

Install Python3.12, a supported Node version (22.22.2+,24.15+,26+) and PostgreSQL. Start PostgreSQL and ensure your local database role can create a database. Commands below target macOS/Linux; Windows users should adapt shell activation/export commands.

```bash
git clone https://github.com/stanleyHayes/neurolab-ai.git
cd neurolab-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
createdb neurolab_judge
python scripts/prepare_judge_demo.py --database-url postgresql:///neurolab_judge
python scripts/audit_datasets.py
python scripts/normalize_ghana.py
set -a; source .env.judge; set +a
python -c 'import os; from neurolab.store import RunStore; RunStore(os.environ["DATABASE_URL"]).close()'
```

Use a dedicated database name. The helper writes `.env.judge` with mode0600 and refuses to overwrite an existing file. It does not create or delete a database, read `.env`, create hosted credentials or contact a model. Keep `.env.judge` private. Run these steps in a fresh checkout without `.env`, `.env.local` or inherited production secrets. The database must be local and ready before services start.

Initialize the database once using the final command above before starting either API or worker. Simultaneous first-time table creation can race in PostgreSQL; do not skip this step.

## Start three local processes

API terminal:

```bash
source .venv/bin/activate
set -a; source .env.judge; set +a
uvicorn neurolab.api:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Worker terminal:

```bash
source .venv/bin/activate
set -a; source .env.judge; set +a
python -m neurolab.worker
```

Frontend terminal:

```bash
set -a; source .env.judge; set +a
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open http://127.0.0.1:3000. To avoid conflicts with existing services, pass `--api-port 8101` to the helper and start Uvicorn on8101; start Next on3101. All three processes must use the same generated environment. Stop them with Ctrl+C when finished. The database persists saved runs; do not delete another user's database during cleanup.

## Register and run the investigation

1. Open Register. Choose a local email-shaped login identifier, display name and password. Email delivery is not required.
2. Read the generated `AUTH_INVITE_CODE` from your private `.env.judge` and enter it in the registration form. It is a local invitation, not a shared published password. Do not record it in screenshots.
3. Open Experiment Studio and click Full Ghana investigation. Keep Deterministic analysis selected; Meta-assisted research should be paused because inference is disabled.
4. Enter: “Investigate drought-related maize patterns in the Ghana combined dataset, including yields, genotype summaries, trait associations and environment sensitivity. Keep uncertainty and limitations visible.”
5. Start investigation. Wait for the worker. A completed full profile produces six scientific artifacts on864plots/72genotypes. Check the actual status instead of assuming every completion criterion has been supported.
6. Open Research Results and Reports. Compare the observed regime means, uncertainty, rankings, trait associations and environment sensitivity. Source citation/hash and design caveats should remain visible.
7. Open cinematic replay to inspect saved tool events. It is replay, not live model reasoning or measured plant animation. Export the evidence for inspection.
8. Sign out and back in; select your saved experiment. A second locally registered account should not inherit the first account's runs.

The observed drought mean is approximately1230.3kg/ha and well-watered mean2616kg/ha, with a descriptive ratio of47%. These describe the published records. Regime/environment confounding prevents causal claims; environment indices are not calendar years, and overlapping source files are not independent replication. Shortlists are research leads, not field recommendations.

## Troubleshooting and optional real inference

An empty results page before creating/selecting a run is expected. If the run remains queued, check the separate worker and its database configuration. If sign-in returns404, confirm the current API is bound to the configured port. If an invite is rejected, ensure the API loaded the same generated file. No email password-reset service is configured; choose credentials you can retain locally.

This mode verifies application features and actual numerical analysis without any hosted service. It does not verify a new Meta response. Real inference is a separate opt-in requiring your own permitted key, verified provider configuration and explicit SQL spending policy; see README and docs/BASETEN_INFERENCE.md. Never copy the entrant's secrets into a public issue or a research objective.
