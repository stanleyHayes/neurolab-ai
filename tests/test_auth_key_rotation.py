"""Generated fixture keys only; no operational secret rotation or model calls."""

import json
import os
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from neurolab.auth import (
    AuthenticationError,
    assert_production_auth_config,
    decode_access_token,
    issue_access_token,
    new_refresh_token,
)


def private_pem(key):
    return key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()


def public_pem(key):
    return (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )


class KeyRotationTests(unittest.TestCase):
    def setUp(self):
        self.old = Ed25519PrivateKey.generate()
        self.new = Ed25519PrivateKey.generate()
        self.old_env = {
            "APP_ENV": "production",
            "AUTH_INVITE_CODE": "private-fixture-invite",
            "AUTH_ED25519_PRIVATE_KEY": private_pem(self.old),
            "AUTH_JWT_KID": "old-v1",
            "AUTH_TOKEN_PEPPER": new_refresh_token(),
            "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS": "{}",
        }
        self.new_env = {
            **self.old_env,
            "AUTH_ED25519_PRIVATE_KEY": private_pem(self.new),
            "AUTH_JWT_KID": "new-v2",
            "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS": json.dumps({"old-v1": public_pem(self.old)}),
        }

    def test_production_requires_invite_while_development_can_close_signup(self):
        for invite in ("", "   "):
            with (
                self.subTest(invite=invite),
                patch.dict(os.environ, {**self.old_env, "AUTH_INVITE_CODE": invite}, clear=True),
                self.assertRaisesRegex(RuntimeError, "Production requires AUTH_INVITE_CODE"),
            ):
                assert_production_auth_config()
        with patch.dict(os.environ, {"APP_ENV": "development", "AUTH_INVITE_CODE": ""}, clear=True):
            assert_production_auth_config()

    def test_staged_rollover_accepts_old_and_new_then_retires_old(self):
        with patch.dict(
            os.environ,
            {
                **self.old_env,
                "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS": json.dumps({"new-v2": public_pem(self.new)}),
            },
            clear=True,
        ):
            assert_production_auth_config()
            old_token = issue_access_token("owner", "session")
        with patch.dict(os.environ, self.new_env, clear=True):
            assert_production_auth_config()
            self.assertEqual(decode_access_token(old_token)["sub"], "owner")
            new_token = issue_access_token("owner", "session")
            self.assertEqual(jwt.get_unverified_header(new_token)["kid"], "new-v2")
            self.assertEqual(decode_access_token(new_token)["sid"], "session")
        with patch.dict(
            os.environ, {**self.new_env, "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS": "{}"}, clear=True
        ):
            with self.assertRaises(AuthenticationError):
                decode_access_token(old_token)
            self.assertEqual(decode_access_token(new_token)["sub"], "owner")

    def test_retained_key_still_requires_signature_issuer_audience_and_lifetime(self):
        with patch.dict(os.environ, self.old_env, clear=True):
            token = issue_access_token("owner", "session")
        claims = jwt.decode(token, options={"verify_signature": False})
        cases = [
            ({**claims, "iss": "untrusted"}, self.old),
            ({**claims, "aud": "untrusted"}, self.old),
            ({**claims, "exp": 1}, self.old),
            (claims, self.new),
        ]
        with patch.dict(os.environ, self.new_env, clear=True):
            for payload, key in cases:
                forged = jwt.encode(
                    payload, key, algorithm="EdDSA", headers={"kid": "old-v1", "typ": "JWT"}
                )
                with self.subTest(payload=payload), self.assertRaises(AuthenticationError):
                    decode_access_token(forged)

    def test_every_required_claim_is_enforced(self):
        with patch.dict(os.environ, self.old_env, clear=True):
            token = issue_access_token("owner", "session")
            claims = jwt.decode(token, options={"verify_signature": False})
            for missing in ("iss", "aud", "sub", "sid", "iat", "nbf", "exp", "jti", "token_type"):
                payload = {key: value for key, value in claims.items() if key != missing}
                signed = jwt.encode(
                    payload, self.old, algorithm="EdDSA", headers={"kid": "old-v1", "typ": "JWT"}
                )
                with self.subTest(missing=missing), self.assertRaises(AuthenticationError):
                    decode_access_token(signed)

    def test_clock_skew_boundaries_use_verifier_clock(self):
        fixed = datetime(2026, 10, 28, tzinfo=UTC)
        timestamp = int(fixed.timestamp())
        with patch.dict(os.environ, self.old_env, clear=True):
            token = issue_access_token("owner", "session")
            claims = jwt.decode(token, options={"verify_signature": False})
            base = {**claims, "iat": timestamp, "nbf": timestamp, "exp": timestamp + 720}
            for field, offset, accepted in (
                ("exp", -14, True),
                ("exp", -15, False),
                ("nbf", 15, True),
                ("nbf", 16, False),
                ("iat", 15, True),
                ("iat", 16, False),
            ):
                payload = {**base, field: timestamp + offset}
                signed = jwt.encode(
                    payload, self.old, algorithm="EdDSA", headers={"kid": "old-v1", "typ": "JWT"}
                )
                with (
                    self.subTest(field=field, offset=offset),
                    patch("jwt.api_jwt.datetime") as clock,
                ):
                    clock.now.return_value = fixed
                    if accepted:
                        self.assertEqual(decode_access_token(signed)["sub"], "owner")
                    else:
                        with self.assertRaises(AuthenticationError):
                            decode_access_token(signed)

    def test_malformed_unsigned_and_wrong_type_headers_are_rejected(self):
        with patch.dict(os.environ, self.old_env, clear=True):
            token = issue_access_token("owner", "session")
            claims = jwt.decode(token, options={"verify_signature": False})
            unsigned = jwt.encode(claims, key="", algorithm="none", headers={"kid": "old-v1"})
            wrong_type = jwt.encode(
                claims, self.old, algorithm="EdDSA", headers={"kid": "old-v1", "typ": "refresh"}
            )
            for invalid in ("", "not-a-token", "a.b.c", token + ".extra", unsigned, wrong_type):
                with self.subTest(token=invalid[:12]), self.assertRaises(AuthenticationError):
                    decode_access_token(invalid)

    def test_unknown_kid_never_selects_a_remote_key(self):
        with patch.dict(os.environ, self.new_env, clear=True):
            token = issue_access_token("owner", "session")
            claims = jwt.decode(token, options={"verify_signature": False})
            attacker = jwt.encode(
                claims,
                self.old,
                algorithm="EdDSA",
                headers={
                    "kid": "https://untrusted.invalid/key",
                    "jku": "https://untrusted.invalid/jwks",
                    "typ": "JWT",
                },
            )
            with patch("urllib.request.urlopen") as network:
                with self.assertRaises(AuthenticationError):
                    decode_access_token(attacker)
                network.assert_not_called()

    def test_bad_overlap_configuration_fails_startup_without_reflecting_key_material(self):
        wrong_type = ec.generate_private_key(ec.SECP256R1())
        duplicate = (
            '{"old-v1":'
            + json.dumps(public_pem(self.old))
            + ',"old-v1":'
            + json.dumps(public_pem(self.old))
            + "}"
        )
        cases = [
            "not-json",
            "[]",
            duplicate,
            json.dumps({"new-v2": public_pem(self.new)}),
            json.dumps({"old-v1": private_pem(self.old)}),
            json.dumps({"old-v1": public_pem(wrong_type)}),
            json.dumps({str(i): public_pem(self.old) for i in range(4)}),
            json.dumps({"invalid kid": public_pem(self.old)}),
            "x" * 16385,
        ]
        for value in cases:
            with (
                self.subTest(value=value[:30]),
                patch.dict(
                    os.environ,
                    {**self.new_env, "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS": value},
                    clear=True,
                ),
            ):
                with self.assertRaises(RuntimeError) as error:
                    assert_production_auth_config()
                self.assertNotIn("BEGIN", str(error.exception))

    def test_active_kid_requires_a_bounded_ascii_identifier(self):
        for kid in ("", "../key", "x" * 81, "key with spaces"):
            with (
                self.subTest(kid=kid),
                patch.dict(os.environ, {**self.old_env, "AUTH_JWT_KID": kid}, clear=True),
                self.assertRaises(RuntimeError),
            ):
                assert_production_auth_config()
