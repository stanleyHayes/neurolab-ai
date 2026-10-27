# Future additions

## Scheduled encrypted offsite backups — deferred by owner, 27 October 2026

The owner explicitly chose to skip this feature for now. Do not create a storage account/bucket, connect Cloudinary/R2/S3, upload database backups to a new provider or schedule backup jobs without a renewed request.

Future scope: automate encrypted backup exports, choose an offsite destination and separate key custody, define retention, monitor job failures, and periodically verify a retrieved backup through a restore rehearsal. Daily backups with 30-day retention were suggested for discussion; no schedule or retention policy was adopted or activated.

No Cloudinary/R2 destination or new paid storage/recovery instance was created. Existing Render recovery and the completed manual hosted-export/local-restore proof remain documented in [the recovery runbook](POSTGRES_RECOVERY_REHEARSAL.md) and `verification/hosted-export-restore-2026-10-27.json`. The encrypted private copy from that rehearsal is not a scheduled or independently managed offsite backup service.

Deferring this addition does not establish production disaster-recovery readiness. Revisit it before a public production release; it is outside the current authorized prototype work until the owner resumes it.

## R2 configuration resumed — 27 October 2026

The owner subsequently reported creating an R2 bucket and requested configuration fields in `.env`, to be filled before adding them to Render. This supersedes the earlier deferral for configuration preparation. Root `.env` now contains private placeholders, with a matching public `.env.example`; existing values were preserved. `BACKUP_ENABLED=false` remains set. No bucket connection, cloud upload, recurring job or lifecycle/deletion policy is active. Actual integration awaits the filled credentials and validation. Daily/30-day values remain proposed defaults, not a deployed policy.

## R2 access verified and Render configuration staged — 27 October 2026

The owner explicitly requested Chrome inspection and confirmed creation of a 30-day Object Read & Write service token restricted to the existing `neurolab-ai` bucket. Native Chrome controls verified that public access/development URL are disabled and no custom domain is assigned. Credentials and a generated encryption key are now saved privately in `.env`; the S3 endpoint is the account endpoint with the bucket separate. The token expires 26 November 2026 and must be rotated before then.

Actual S3 bucket/list checks and a non-sensitive object upload/download/cleanup succeeded. The ten configuration values are also stored in the protected Render Production environment group `neurolab-backups`, with zero linked services and `BACKUP_ENABLED=false`. Vercel was unchanged. No backup data has been uploaded and no recurring backup implementation/job has been deployed or enabled. See `verification/r2-browser-setup-2026-10-27.json`. Execution, scheduling and encrypted R2 upload/retrieval/restore acceptance remain the next integration work.
