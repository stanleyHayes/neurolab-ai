# PostgreSQL snapshot restore rehearsal

This runbook separates verified data recovery from a production cutover. The current hosted rehearsal used a logical export of the existing Render `neurolab-db`, restored into a separate, temporary PostgreSQL 18 cluster on the operator's computer. The live API, worker, database URL and database public-access allowlist were not changed.

## Current evidence

`verification/hosted-export-restore-2026-10-27.json` records the provider recovery status, export timestamp/hash, restore result and limitations. All 15 public application tables matched the export's row counts and order-independent COPY-content digests. Column and sequence inventories were checked as well. The snapshot contains two runs, eight artifacts and 85 events, and its run source hashes match the canonical Ghana source. There are no public sequences in this snapshot; non-empty sequence behavior has separate unit coverage.

The restored cluster used a private Unix socket, SCRAM authentication and no TCP listener. Verification used a read-only transaction. It was stopped and removed after verification. Generated plaintext working files were removed after the retained encrypted archive was decrypted and its hash rechecked. The archive and its separate key file are private owner-only files outside the repository. Same-host key storage is not independently managed key custody or an established long-term offsite policy.

## Provider recovery boundary

The actual Render API returned `recoveryStatus=AVAILABLE`; the earliest available timestamp is recorded in the evidence, rather than assuming a full advertised recovery window for a newly created database. The [recovery-status API](https://api-docs.render.com/reference/retrieve-postgres-recovery-info) is read-only.

The rehearsal created one [logical export](https://api-docs.render.com/reference/create-postgres-export) and subsequently reused it. Signed download URLs were retained only in private operator state. Render documents a seven-day retention period for logical exports; longer retention requires a separately managed destination. PITR availability is different from actually rehearsing a managed PITR restore or switching services to a recovery instance. See [Render recovery and backups](https://render.com/docs/postgresql-backups).

## Repeat the rehearsal

1. Confirm the exact owned database ID and inspect existing exports. Reuse an accepted/in-progress export after a timeout; do not blindly submit another request. Record the selected export ID and timestamp, keeping its signed URL private.
2. Download the export into an owner-only working directory outside the checkout. Retain an authenticated encrypted copy and protect its encryption key separately. The recorded rehearsal used the existing `cryptography` dependency's [Fernet authenticated encryption](https://cryptography.io/en/latest/fernet/); it verified decryption against the original archive SHA-256 before removing working data. Do not publish source SQL, rows, password hashes, URLs, connection strings or keys.
3. Extract only the expected regular files/directories into that private directory, rejecting escaping paths, links and excessive uncompressed size. Find the directory containing `toc.dat`.
4. Create a **new empty** local PostgreSQL cluster/database for the rehearsal, using a private Unix socket and a name starting `neurolab_restore_`. Keep TCP disabled. Use a private `PGPASSFILE` rather than placing a password or connection URL in command arguments. Use the same PostgreSQL major version as the export. Only restore an approved first-party archive: restoration executes its schema code.
5. Restore the archive and produce a data-only comparison script:

   ```sh
   pg_restore --host="$RESTORE_SOCKET_DIR" --port="$RESTORE_PORT" \
     --username=neurolab_restore --dbname="$RESTORE_DB" \
     --no-owner --no-privileges --exit-on-error "$ARCHIVE_DIRECTORY"

   pg_restore --data-only --no-owner --no-privileges \
     --file="$PRIVATE_DIR/export-data.sql" "$ARCHIVE_DIRECTORY"
   ```

   These commands require the empty rehearsal target; they do not use `--clean`, `--create` or a live database URL. See [PostgreSQL pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html).
6. Inject the rehearsal DSN securely as `RESTORE_DATABASE_URL`, then run:

   ```sh
   python3 scripts/verify_postgres_restore.py \
     --dump-data "$PRIVATE_DIR/export-data.sql"
   ```

   The verifier accepts only an owned private Unix-socket directory and the rehearsal database name prefix. It rejects service/host-address redirection, enforces read-only connection options, reads ordinary public-table data via COPY TO, and compares every table/column/row digest and sequence state. It never executes the data script, creates schema, restores a database or prints row values/credentials. Unsupported data forms fail closed. COPY nulls, empty strings, escapes and duplicate row multiplicity remain distinct; row order is deliberately ignored. Data scripts are limited to 128 MiB. The helper is scoped to NeuroLab's ordinary public tables/sequences, not arbitrary extensions or large objects.
7. Verify the canonical source hash and saved job state, then stop the disposable cluster. Remove generated plaintext and temporary cluster files only after confirming the retained encrypted archive round trip. Record counts, hashes and outcomes without including private data.

## Remaining production gates

The source repository and immutable datasets are part of recovery; a database snapshot alone does not replace the exact application release, Ed25519 key, refresh-hash pepper and other separately held runtime secrets. Their distribution/retirement needs its own procedure.

This rehearsal does **not** prove a Render PITR cutover, cross-region failure recovery, target RPO/RTO, scheduled encrypted offsite retention, independent key custody, monitoring/alert delivery or rollback under live traffic. The owner explicitly deferred scheduled encrypted offsite backups on 27 October 2026; see [Future additions](FUTURE_ADDITIONS.md). A destination, retention policy and renewed request are required before resuming that feature. The app stays invite-gated, and inference stays paused.

## R2 configuration fields — prepared, disabled

The owner resumed setup after reporting an existing R2 bucket and requested private `.env` fields before Render configuration. Fill `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`, `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` using the existing account/bucket. `R2_ACCOUNT_ID` is optional for S3-only access because the endpoint includes it. A general Cloudflare API token is not needed for S3 object operations; bucket-level settings may require separate dashboard permissions. The [Cloudflare S3 setup guide](https://developers.cloudflare.com/r2/get-started/s3/) describes bucket-scoped Object Read & Write credentials and the S3 endpoint. Do not use a global Cloudflare API key or `NEXT_PUBLIC_` variables. Keep the bucket private.

`BACKUP_ENABLED=false` stays in place until integration and encrypted recovery validation pass. `R2_BACKUP_PREFIX=neurolab/postgres/`, `BACKUP_RETENTION_DAYS=30` and `BACKUP_SCHEDULE_UTC="0 2 * * *"` are proposed defaults only. `BACKUP_ENCRYPTION_KEY` may remain blank for secure generation before enabling; keep the key outside R2. These are reserved integration fields, not a claim that a recurring backup implementation is already running. After the owner fills them, validate and configure only the appropriate Render backend/backup runtime, keeping Vercel free of these secrets.

## Verified R2 access and staged Render group

Chrome inspection and S3 operations now verify access to the existing private bucket. User-approved bucket-only credentials expire 26 November 2026; rotate before that date. They are saved in private `.env` and the unlinked Render Production group `neurolab-backups`, together with the encryption key and disabled configuration. Actual non-sensitive write/read/cleanup passed. No database backup object or recurring job is active; the end-to-end R2 encrypted backup/recovery path still needs execution and validation before activation. See `verification/r2-browser-setup-2026-10-27.json`.
