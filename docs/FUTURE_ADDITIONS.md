# Future additions

## Scheduled encrypted offsite backups — deferred by owner, 27 October 2026

The owner explicitly chose to skip this feature for now. Do not create a storage account/bucket, connect Cloudinary/R2/S3, upload database backups to a new provider or schedule backup jobs without a renewed request.

Future scope: automate encrypted backup exports, choose an offsite destination and separate key custody, define retention, monitor job failures, and periodically verify a retrieved backup through a restore rehearsal. Daily backups with 30-day retention were suggested for discussion; no schedule or retention policy was adopted or activated.

No Cloudinary/R2 destination or new paid storage/recovery instance was created. Existing Render recovery and the completed manual hosted-export/local-restore proof remain documented in [the recovery runbook](POSTGRES_RECOVERY_REHEARSAL.md) and `verification/hosted-export-restore-2026-10-27.json`. The encrypted private copy from that rehearsal is not a scheduled or independently managed offsite backup service.

Deferring this addition does not establish production disaster-recovery readiness. Revisit it before a public production release; it is outside the current authorized prototype work until the owner resumes it.

## R2 configuration resumed — 27 October 2026

The owner subsequently reported creating an R2 bucket and requested configuration fields in `.env`, to be filled before adding them to Render. This supersedes the earlier deferral for configuration preparation. Root `.env` now contains private placeholders, with a matching public `.env.example`; existing values were preserved. `BACKUP_ENABLED=false` remains set. No bucket connection, cloud upload, recurring job or lifecycle/deletion policy is active. Actual integration awaits the filled credentials and validation. Daily/30-day values remain proposed defaults, not a deployed policy.
