# Access JWT signing key rotation

## Supported boundary

The API signs new access JWTs only with `AUTH_ED25519_PRIVATE_KEY` and `AUTH_JWT_KID`. It verifies the current key plus a maximum of three explicitly configured verify-only Ed25519 public keys from `AUTH_ED25519_PREVIOUS_PUBLIC_KEYS`. This is a JSON object mapping key IDs to public PEM strings. It may temporarily include an upcoming key during a staged rollout as well as previous keys.

Key IDs use 1–80 ASCII letters, digits, dots, underscores or hyphens. Startup rejects malformed/oversized JSON, duplicate IDs, current-ID collisions, too many keys, private PEMs, unsupported key types and invalid public material. Invalid configurations fail closed; they do not select another key. JWT `kid` selects only from this configured map. No token-provided URL/JWK, network key discovery or arbitrary algorithm is used. EdDSA signature, issuer, audience, type, required claims and lifetime checks still apply. Active user/session and resource ownership remain required after JWT validation.

This provides local rotation capability, not a claim that deployed secrets have been rotated. No operational keys or HMAC pepper were changed while building/testing this feature. Workers do not need API signing/verification material.

## Existing local development sessions

When the private key is unset in development, each API process generates an ephemeral signer. Its old public key is not recoverable from configuration after that process exits. Do not describe restarting that process as a verified planned rollover, or use it as a multi-replica production setup. The current local primary/review APIs were observed in this mode and were left running during this contribution; their operational keys were not replaced. Rehearsals use separately generated, stable fixture keys in disposable production-profile APIs.

A future persistent-key local/target rollout requires an explicit configuration plan and fresh sign-in/refresh checks. This feature does not silently write generated private keys to disk or change the local `.env`.

## Planned rotation procedure

Use generated real secrets only in the target secret manager. Do not put private keys, tokens or `.env` contents in Git, command output, screenshots, video, tickets or evidence files. The JSON overlap contains public keys only, but it is still controlled server configuration. Use a JSON encoder to represent PEM newlines; do not hand-escape multiline secret values.

1. **Inventory and prepare.** Identify all API instances, current key ID, issuer/audience and last rollout state. Generate a new Ed25519 private/public pair and a new distinct ID. Back up/rehearse target configuration using the operator's secret-management procedure. Keep signing changes separate from the HMAC pepper, service credential and database changes.
2. **Stage verification first.** Keep the old active private key/ID. Add the upcoming public key under its new ID in every API's overlap JSON and restart/roll out those instances. Confirm all instances accept an authorized test JWT signed by the new key and still accept current sessions. This prevents old replicas rejecting new tokens during rollout. Do not expose a public token-minting endpoint to perform this check.
3. **Activate the new signer.** Set the new private PEM and new current ID on rolling instances. Replace their overlap JSON with the previous public key under its old ID; the current ID must not also occur in overlap. Retain issuer/audience and `AUTH_TOKEN_PEPPER` unchanged. Old staged replicas can verify new JWTs; new replicas can verify old ones. Check that login and refresh issue the new ID and that two-account isolation/CSRF behavior remains intact.
4. **Finish replacing old issuers.** Confirm no API instance can still issue with the old private key. Remove that private key from active runtime access. Record the last possible old issuance time, deployment IDs and public-key fingerprints without logging secrets. Refresh sessions are opaque HMAC-protected values; they can rotate into access JWTs signed with the new key without retaining the old private key.
5. **Drain the overlap.** Current access TTL is 12 minutes with 15 seconds of verification leeway. Wait at least that interval after the last possible old issuance, plus an operator-chosen clock/rollout margin; 15 minutes is a practical minimum only if that covers the actual rollout/clock conditions. Do not start the timer while old replicas still issue. Verify clocks and target token timing instead of assuming them.
6. **Retire the old verifier.** Remove the old ID/public PEM from all API overlap maps and roll out again. Confirm old-key tokens are rejected and new-key sessions/refresh still work. The overlap has no automatic time-based removal; operators must complete this step. Follow the secret manager's approved retention/destruction policy for old private material.

If rotation fails before retirement, restore the last reviewed configuration consistently. Do not silently reintroduce a compromised or intentionally retired key. The application does not automate secret distribution, detect configuration drift across deployed instances or prove rollback safety.

## Suspected compromise

Do not use the normal grace period for a suspected signing-key compromise. Remove the compromised verifier/signer from all instances promptly, replace signing material, and follow incident response and session-revocation procedures. A stolen refresh cookie/session is a separate risk. Pepper rotation invalidates refresh/CSRF hashes and other keyed records; this feature does not rotate or migrate the pepper. Coordinate any such change explicitly rather than swapping it with the signing key.

## Evidence and remaining checks

`tests/test_auth_key_rotation.py` uses generated fixture keys to exercise staged verification, active-key issuance, overlap/retirement, signature/issuer/audience/expiry checks, unknown/remote-looking IDs and malformed configuration. The authenticated API regression exercises an old access token through overlap, refresh into the new signer and continued new-token access after retirement. No real local session keys change in these tests.

Production acceptance still requires the actual secret manager, multi-instance deployment, TLS/browser cookies, signed-out/fresh-account checks, SSE authorization during rollout, monitoring, incident procedures and reviewed rollback/retirement records. Local key tests do not make signup public or establish production readiness. Meta inference remains paused and is unrelated to signing rotation.
