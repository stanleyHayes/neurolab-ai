"""Generated fixture keys only; no operational secret rotation or model calls."""

import json
import os
import unittest
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
