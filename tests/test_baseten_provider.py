"""Programmed Baseten boundary tests with real SQL admission; not live inference."""

import io
import json
import os
import unittest
import uuid
from unittest.mock import Mock, patch

from neurolab.deployment_runtime import configure_deployment, configure_replay
from neurolab.model_configuration import BASETEN_ENDPOINT, BASETEN_MODEL, model_configuration
from neurolab.model_spend import ModelSpendError, ModelSpendGuard, SpendPolicy, apply_policy
from neurolab.providers import ModelProviderError, OpenAICompatibleAdapter, adapter_status
from neurolab.store import RunStore
from tests.test_providers import SPEND_ENV

SETTINGS = {
    **SPEND_ENV,
    "MODEL_PROVIDER": "baseten",
    "BASETEN_API_KEY": "synthetic-baseten-secret",
    "BASETEN_MODEL_API_BASE_URL": BASETEN_ENDPOINT,
    "BASETEN_MODEL_ID": BASETEN_MODEL,
    "BASETEN_MODEL_VERIFIED": "true",
    "META_MODEL_API_KEY": "synthetic-other-vendor-secret",
    "META_MODEL_VERIFIED": "true",
    "MODEL_INFERENCE_ENABLED": "true",
    "MODEL_MAX_RUN_TOKENS": "100000",
    "MODEL_MAX_OUTPUT_TOKENS": "2000",
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ok"],
    "properties": {"ok": {"type": "boolean"}},
}


def function_call(arguments='{"ok":true}', name="submit_research_action"):
    return {"type": "function", "function": {"name": name, "arguments": arguments}}


class BasetenProviderTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, SETTINGS, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.store = RunStore(":memory:")
        self.addCleanup(self.store.close)
        self.owner = self.store.create_user("baseten@example.test", "fixture", "Test")["user_id"]

    def model(self):
        return OpenAICompatibleAdapter.from_environment().bind_spending(
            self.store, self.owner, "smoke:" + str(uuid.uuid4())
        )

    def response(self, calls, finish="tool_calls"):
        response = Mock(status=200)
        response.getheader.return_value = None
        response.read.return_value = json.dumps(
            {
                "choices": [
                    {"finish_reason": finish, "message": {"content": None, "tool_calls": calls}}
                ]
            }
        ).encode()
        connection = Mock()
        connection.getresponse.return_value = response
        return connection

    def test_selected_vendor_has_separate_key_verification_and_truthful_identity(self):
        model = self.model()
        self.assertEqual((model.provider, model.model_id), ("baseten", BASETEN_MODEL))
        self.assertEqual(model.api_key, SETTINGS["BASETEN_API_KEY"])
        self.assertNotIn(model.api_key, repr(model_configuration()))
        self.assertEqual(adapter_status()["provider"], "baseten")
        with patch.dict(os.environ, {"BASETEN_MODEL_VERIFIED": "false"}):
            self.assertFalse(adapter_status()["enabled_for_runs"])
        with patch.dict(os.environ, {"BASETEN_API_KEY": ""}):
            self.assertFalse(adapter_status()["configured"])
            with self.assertRaises(ModelProviderError):
                self.model()

    def test_only_approved_meta_open_model_and_baseten_endpoint_are_accepted(self):
        for change in [
            {"BASETEN_MODEL_ID": "another-model"},
            {"BASETEN_MODEL_ID": "meta-models/muse-spark-open"},
            {"BASETEN_MODEL_API_BASE_URL": "https://foreign.invalid/chat"},
            {"BASETEN_MODEL_API_BASE_URL": BASETEN_ENDPOINT + "?token=secret"},
        ]:
            with self.subTest(change=change), patch.dict(os.environ, change):
                self.assertFalse(adapter_status()["enabled_for_runs"])
                with self.assertRaises(ModelProviderError):
                    self.model()
                with self.assertRaises(ModelSpendError):
                    SpendPolicy.from_environment()

    def test_forced_single_function_schema_and_full_wire_bytes_are_reserved(self):
        model = self.model()
        connection = self.response([function_call()])
        with patch("neurolab.providers.http.client.HTTPSConnection", return_value=connection):
            self.assertEqual(
                model.generate_structured([{"role": "user", "content": "α"}], SCHEMA, timeout=2),
                {"ok": True},
            )
        sent = connection.request.call_args.kwargs
        self.assertIsInstance(sent["body"], bytes)
        self.assertIn("α".encode(), sent["body"])
        body = json.loads(sent["body"])
        self.assertNotIn("response_format", body)
        self.assertEqual(body["tools"][0]["function"]["parameters"], SCHEMA)
        self.assertEqual(body["tool_choice"]["function"]["name"], "submit_research_action")
        self.assertFalse(body["parallel_tool_calls"])
        self.assertEqual(body["reasoning_effort"], "low")
        self.assertEqual(body["max_tokens"], 2000)
        self.assertEqual(sent["headers"]["Authorization"], "Bearer " + SETTINGS["BASETEN_API_KEY"])
        row = self.store._execute("SELECT * FROM model_spend_reservations").fetchone()
        self.assertEqual(row["input_tokens"], len(sent["body"]) + 1)
        self.assertEqual(row["outcome"], "completed")

    def test_wrong_missing_multiple_malformed_and_out_of_schema_calls_fail_closed(self):
        invalid = [
            [],
            [function_call(), function_call()],
            [function_call(name="run_shell")],
            [function_call(arguments="not json")],
            [function_call(arguments='{"ok":"yes"}')],
            [function_call(arguments='{"ok":true,"extra":1}')],
            [function_call(arguments={"ok": True})],
        ]
        for calls in invalid:
            with self.subTest(calls=calls):
                model = self.model()
                with (
                    patch(
                        "neurolab.providers.http.client.HTTPSConnection",
                        return_value=self.response(calls),
                    ),
                    self.assertRaises(ModelProviderError),
                ):
                    model.generate_structured([], SCHEMA, timeout=2)

    def test_truncated_function_never_becomes_a_valid_response(self):
        model = self.model()
        with (
            patch(
                "neurolab.providers.http.client.HTTPSConnection",
                return_value=self.response([function_call()], "length"),
            ),
            self.assertRaisesRegex(ModelProviderError, "output-token"),
        ):
            model.generate_structured([], SCHEMA, timeout=2)

    def test_cross_vendor_policy_requires_explicit_cas_and_retains_reservations(self):
        with patch.dict(os.environ, {"MODEL_PROVIDER": "meta"}):
            old = SpendPolicy.from_environment()
        apply_policy(self.store, old, "empty")
        ModelSpendGuard(self.store, self.owner, "smoke:prior", "meta", "fixture", old).reserve(1, 1)
        model = self.model()
        with patch("neurolab.providers.http.client.HTTPSConnection") as transport:
            with self.assertRaisesRegex(ModelProviderError, "policy differs"):
                model.generate_structured([], SCHEMA, timeout=2)
            transport.assert_not_called()
        apply_policy(self.store, SpendPolicy.from_environment(), old.digest)
        self.assertEqual(
            self.store._execute("SELECT COUNT(*) AS n FROM model_spend_reservations").fetchone()[
                "n"
            ],
            1,
        )
        with patch(
            "neurolab.providers.http.client.HTTPSConnection",
            return_value=self.response([function_call()]),
        ):
            self.assertEqual(self.model().generate_structured([], SCHEMA, timeout=2), {"ok": True})

    def test_worker_retains_only_selected_vendor_key_and_replay_removes_both(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://fixture.invalid/db",
                "AUTH_ED25519_PRIVATE_KEY": "fixture",
            },
        ):
            configure_deployment(worker=True)
            self.assertEqual(os.environ["BASETEN_API_KEY"], SETTINGS["BASETEN_API_KEY"])
            self.assertNotIn("META_MODEL_API_KEY", os.environ)
            self.assertNotIn("AUTH_ED25519_PRIVATE_KEY", os.environ)
            configure_replay(worker=True)
            self.assertNotIn("BASETEN_API_KEY", os.environ)

    def test_operator_smoke_uses_selected_vendor_and_prints_safe_actual_metadata(self):
        from scripts.smoke_meta_provider import main

        output = io.StringIO()
        with (
            patch.dict(os.environ, {"MODEL_SMOKE_OWNER_USER_ID": self.owner}),
            patch("scripts.smoke_meta_provider.RunStore", return_value=self.store),
            patch(
                "neurolab.providers.http.client.HTTPSConnection",
                return_value=self.response([function_call()]),
            ),
            patch("sys.stdout", output),
        ):
            code = main()
        self.assertEqual(code, 0)
        self.assertIn('"provider": "baseten"', output.getvalue())
        self.assertIn("BASETEN_MODEL_VERIFIED=true", output.getvalue())
        self.assertNotIn(SETTINGS["BASETEN_API_KEY"], output.getvalue())
