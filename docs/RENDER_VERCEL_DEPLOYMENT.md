# Render backend and Vercel frontend

This is the owner's current hosting choice, superseding the earlier all-Vercel proposal. GitHub `stanleyHayes/neurolab-ai`, branch `main`, contains both parts. The application code is MIT licensed. The live frontend is `https://neurolab-ai.vercel.app` and API is `https://neurolab-api.onrender.com`. Both Render services and PostgreSQL are provisioned in the NeuroLab AI project. Hosted HTTP/auth/queue/science/SSE checks are recorded in `verification/hosted-deployment-2026-10-27.json`; browser and wider operational acceptance remain open.

The deployed resources were created via the public Render API using the Blueprint declarations. No managed Blueprint instance/autosync was created. Do not apply a second fresh Blueprint in this workspace expecting it to represent the existing resources automatically. Auto-deploy is off; use the recorded service IDs for explicit releases.

## Components

- **Render web service `neurolab-api`:** Dockerized FastAPI, production authentication, PostgreSQL persistence, redacted `/health`. The container binds `0.0.0.0:$PORT` and disables Uvicorn proxy-header trust.
- **Render background worker `neurolab-worker`:** Dockerized SQL queue consumer, no HTTP listener. It shares the backend database, drains on SIGTERM and has a 210-second shutdown allowance. Started work is never automatically retried after lease loss.
- **Render PostgreSQL `neurolab-db`:** persistent backing store on the same region/private network. The Blueprint disables public database IP access. No SQLite or filesystem persistence is used for production state.
- **Vercel:** standard Next.js deployment. Browser requests go to same-origin `/api/*`; the server-side proxy calls the Render HTTPS API with its service bearer and the user's first-party credentials. No Vercel Services, Daemons, service bindings or Python runtime is needed.

Unlike the earlier Vercel private service plan, the Render API is internet reachable over HTTPS. `/health` exposes only status; all other API routes require the service credential, and private research routes additionally require the verified owner's JWT. Provider/signing secrets never belong in frontend public variables. Cross-origin browser access to FastAPI is unnecessary: keep the BFF/CSRF and HttpOnly-cookie flow.

## Render Blueprint

Import this repository's `render.yaml` through Render's New Blueprint flow. It declares both Docker services and PostgreSQL, all on `main` in Frankfurt. The proposed compute/database plans are paid resources; inspect Render's displayed costs before applying. Preparing/validating the file creates no resources; the owner subsequently explicitly authorized deployment and the declared baseline resources are now running. Auto-deploy is off so a source push does not automatically roll out an unverified release.

The official [Blueprint reference](https://render.com/docs/blueprint-spec) describes generated secrets, database connection references and prompted variables. The Blueprint generates a service bearer, token pepper and private invite. Supply a **new deployment-only Ed25519 private key** and stable JWT issuer when prompted. Preserve the generated values across redeployments. Do not reuse or rotate the existing local ephemeral signer.

The Blueprint references the API's Render external hostname. Direct platform provisioning can also derive a single exact allowlisted hostname from Render's own `RENDER_EXTERNAL_HOSTNAME` when no explicit allowlist is configured; malformed/wildcard values are rejected and request headers are never trusted for this. If a custom domain is added, update the explicit allowlist and verify health-check host handling. Keep forwarded-client-IP trust unset until the actual ingress chain has been verified. Both services use the same internal PostgreSQL connection reference. The worker receives no signing key, pepper, invite or service credential; its deployment entrypoint also removes inherited credentials defensively.

The deployment entrypoints force replay mode and reject a missing/non-PostgreSQL database. Do not upload provider keys; inference remains paused regardless of a mistakenly enabled environment flag. Numeric tools continue to use immutable Ghana source data. Render commit metadata supplies the revision when Git files are absent, with source/module hashes retained.

## Vercel configuration

Import the same repository with root directory `.` and framework Next.js. `vercel.json` defines only frontend install/build settings. Configure these **server-side** variables from `deploy/vercel.env.example`:

1. `RESEARCH_API_URL`: the actual Render API HTTPS URL, without inventing a hostname from the service name.
2. `API_BEARER_TOKEN`: exactly the generated value on the Render API service. Copy it securely; do not prefix it with `NEXT_PUBLIC_`, publish it, or put it in screenshots.

Do not put the database URL, signing key, token pepper, invite or provider keys on Vercel. Preview deployments must not share production credentials/data by default; use a separate protected backend/environment for preview acceptance. A frontend preview is not a complete production-backend rollout.

## Checks before opening access

Render's [health checks](https://render.com/docs/health-checks) need an unauthenticated `GET /health` returning a redacted 200. The API still requires service authentication elsewhere. Verify that distinction through the real URL. Render [shutdown handling](https://render.com/docs/deploys) must allow the bounded current job to drain; both services request 210 seconds.

After applying the Blueprint and configuring Vercel, verify API health, worker logs/lease claims, shared database, production key/refresh lifecycle, account creation with private invite, two-owner isolation, CSRF, secure cookies, persisted six-tool replay, SSE reconnect, cancellation, worker restart/interruption and report export. Check backing-database restore/retention, alerts and rollback. Keep the application invite-gated and protected until those tests pass. No provider calls are needed.

## Local verification

```sh
render blueprints validate render.yaml --output json
make quality
docker build -f Dockerfile -t neurolab-render-api:review .
docker build -f Dockerfile.worker -t neurolab-render-worker:review .
```

Blueprint validation and local Docker/PostgreSQL checks do not create infrastructure or establish hosted acceptance. Actual service IDs/URLs, Vercel project/environment, production secrets, database provisioning and release evidence must be recorded after deployment. Earlier Vercel-only evidence remains historical, not the current topology.

## Hosted snapshot recovery rehearsal

A logical export of the actual Render database was restored in a separate local PostgreSQL 18 cluster and compared read-only against every public table/column/content digest and sequence state. See [the recovery runbook](POSTGRES_RECOVERY_REHEARSAL.md) and `verification/hosted-export-restore-2026-10-27.json`. Provider PITR availability and this snapshot restore are verified separately from a managed PITR cutover, scheduled offsite retention, key custody, alerts and target RPO/RTO. The live database and its empty public-access allowlist were unchanged.

The owner subsequently deferred scheduled encrypted offsite backups on 27 October 2026. See [Future additions](FUTURE_ADDITIONS.md); no new storage destination or recurring backup job is configured.
