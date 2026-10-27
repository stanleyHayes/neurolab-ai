# User data isolation

## Resources in the current product

The only mutable persisted user resource in this prototype is a research run, including its nested report JSON, artifact rows, and event rows. There is no experiment table, private upload, saved finding table, or server-side export store yet. The authenticated run contract is therefore the complete current isolation surface; future private resource types must add an owner foreign key and owner-filtered reads/writes before UI exposure.

## Enforcement

1. FastAPI validates the signed short-lived JWT and checks user/session activity on every protected request.
2. Run creation writes the JWT subject as `owner_user_id`; request bodies cannot supply an owner.
3. Lookup and list methods include owner equality in SQL. Inaccessible resources are indistinguishable from absent IDs (404).
4. Nested event/artifact/report access first resolves the owner-scoped parent. Cancellation is owner-scoped.
5. SSE validates parent ownership before opening and rechecks both owner and active session each poll/reconnect. Bearer tokens never appear in event URLs.
6. Shared Ghana dataset/profile data is curated read-only, not user-owned content.
7. Existing run rows get NULL owner on migration and are intentionally quarantined from user-visible lists. Operator-approved mapping is required before any legacy transfer.

## Direct-object reference test matrix

The API tests create two independent accounts. Account B sees no runs and gets 404 for A's run, report, artifacts, events, and cancellation; A continues to read the same resources. Unowned legacy rows are not visible to A. Anonymous requests are rejected. The integration suite exercises actual FastAPI/SQLite/TestClient paths, not only repository helper functions.

## Extension requirements

For any future uploads, exports, or findings:

- Store `owner_user_id NOT NULL` with an FK and owner-scoped index; include owner ID in every object key/path and authorization query.
- Store files outside web root using random server-generated names; validate size/content and never use user filenames as paths.
- Authorize before streaming/download and recheck on reconnect/async jobs.
- Keep logs free of passwords/tokens and avoid logging raw research content unless justified and access-controlled.
- Test cross-account guessed identifiers, nested resources, mutation, deletion, retries, and pagination.