# Vercel deployment preparation

Owner selected Vercel for application hosting, GitHub `stanleyHayes/neurolab-ai`, branch `main`, MIT application code. This is a prepared configuration, not a successful hosted deployment or public-production approval.

## Prepared layout

`vercel.json` defines Next.js `web`, native Python `research`, and a containerized `research-worker` Daemon. Public requests route to `web` only. Its `RESEARCH_API_URL` binding reaches the private backend; `/api/*` continues through the existing authenticated same-origin BFF, including service credential, user JWT, CSRF and HttpOnly cookies. Do not add a public rewrite to `research` or bypass the BFF.

Vercel documents private service bindings and public routing in its [Services guide](https://vercel.com/kb/guide/vercel-services). The [Daemons documentation](https://vercel.com/docs/daemons) describes production workers, ephemeral storage and termination handling. Services/Daemons are beta features; check account availability before deploying. Daemons currently do not run in previews or `vercel dev`, so a preview is not an end-to-end worker acceptance environment. No alternate hosting provider is required by this configuration.

The owner-requested replay profile explicitly disables model inference and inline workers, removes provider keys, and rejects a non-PostgreSQL database before loading the API/worker. The worker drops inherited signing, refresh-pepper, invite and service credentials. It retains database access and existing lease/fencing behavior. SIGTERM/SIGINT stops polling after the current claim; shutdown grace is 210 seconds for an at-most-180-second investigation plus cleanup. Interrupted work is not automatically retried.

Python is pinned to 3.12 via `.python-version` and the worker image. The BFF and Python service have 300-second function ceilings; verify Fluid compute and actual project limits. Native streaming still needs deployed SSE/reconnect acceptance. The container copies only runtime code, schemas, requirements and data; local environments and recordings are excluded. Runtime provenance uses a validated Vercel Git SHA only when Git metadata is unavailable; exact module/source hashes remain recorded.

## Configure before deployment

1. Import the GitHub repository into the intended Vercel team/project. Use `main`, repository root and Services support. The existing Next.js project layout is retained; do not select a frontend-only preset that ignores `services`/`daemons`.
2. Provision PostgreSQL through Vercel Marketplace and attach its connection string to `DATABASE_URL`. API and worker must share the intended database. Local SQLite, local PostgreSQL URLs and daemon filesystem storage are unsuitable. Use an isolated database/branch and distinct signing, pepper and service secrets for preview experiments. Do not share production sessions or data with previews.
3. Configure the server-only variables listed in `deploy/vercel.env.example`. Generate a new deployment signing key, independent token pepper, service bearer and private invite. Never copy the local ephemeral API key or rotate an existing local signer. Keep production secrets in Vercel, outside source/public variables. No production secrets have been generated or uploaded by this preparation.
4. Set exact issuer and allowed hosts for the real project/private transport. Verify the host received over the binding before opening access; do not use `*` to make a failed check pass. Keep aggregate peer quotas unless the real Vercel ingress/header trust chain is verified.
5. Enable required beta features and confirm worker availability/capacity in the selected account. The initial worker region is `iad1`; align service/database placement as appropriate before production. Check daemon billing/capacity; one configured instance is not a billing approval or availability proof.
6. Keep Deployment Protection and invite gating while validating. Deploy the complete release only after environment/database/feature admission succeeds. Do not mistake a frontend build for full app acceptance.

The CLI is installed and authenticated locally, but the read-only project listing showed no matching NeuroLab project at preparation time. No project was created, production deployment invoked, database provisioned, or secret uploaded. A hosted rollout still needs the actual Vercel project and persistent database configuration.

## Local commands and actual acceptance

```sh
make quality
docker build -f Dockerfile.worker -t neurolab-vercel-worker:review .
# After configuring an isolated persistent database/environment:
vercel dev -L
# Run the worker separately locally; vercel dev does not start Daemons.
python -m neurolab.vercel_worker
```

The worker container's read-only/no-network source-loading check verified 864 canonical records and the expected SHA-256. Runtime unit tests verify replay admission, secret removal, queue stopping and commit metadata validation. These checks do not establish Vercel routing or managed-database connectivity.

On the actual protected deployment, verify native API startup, no direct public research ingress, signed-out behavior, two-owner isolation, CSRF/cookies, source hash, real six-tool replay, daemon claim/heartbeat/finalization, SSE reconnect, cancellation, bounded shutdown and restart without duplicate work. Confirm report artifacts survive instance turnover. Verify production health redaction, stable signing keys/refresh lifecycle, shared quotas, backing database backups/restore, monitoring and rollback. Use zero provider calls. Only then record hosted evidence and assess the remaining public release gates.
