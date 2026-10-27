"""Model boundary contracts use fixtures only; no network or live inference."""

import json
import os
import unittest
from unittest.mock import Mock, patch

from neurolab.providers import ModelProviderError, OpenAICompatibleAdapter, adapter_status

MESSAGES = [{"role": "user", "content": "Fixture-only structured action request"}]
SCHEMA = {"type": "object"}


def adapter():
    return OpenAICompatibleAdapter(
        endpoint="https://provider.invalid/v1/chat/completions",
        api_key="fixture-only-private-value",
        model_id="fixture",
        max_output_tokens=100,
    )


class ProviderContractTests(unittest.TestCase):
    def test_success_is_json_with_server_only_credentials_and_reserved_budget(self):
        model = adapter()
        response = Mock(status=200)
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": '{"action":"dataset_profile"}'}}]}
        ).encode()
        connection = Mock()
        connection.getresponse.return_value = response
        with patch("neurolab.providers.http.client.HTTPSConnection", return_value=connection):
            result = model.generate_structured(MESSAGES, SCHEMA, timeout=2)
        self.assertEqual(result, {"action": "dataset_profile"})
        self.assertGreater(model.tokens_reserved, model.max_output_tokens)
        request = connection.request.call_args
        self.assertEqual(
            request.kwargs["headers"]["Authorization"], "Bearer fixture-only-private-value"
        )
        sent = json.loads(request.kwargs["body"])
        self.assertEqual(sent["messages"], MESSAGES)
        self.assertTrue(sent["response_format"]["json_schema"]["strict"])
        connection.close.assert_called_once()

    def test_http_transport_and_malformed_responses_fail_without_exposing_secrets(self):
        cases = [
            (401, b"private-provider-body", None),
            (429, b"private-provider-body", None),
            (500, b"private-provider-body", None),
            (200, b"not-json", None),
            (200, b'{"choices":[]}', None),
            (200, b'{"choices":[{"message":{"content":"[]"}}]}', None),
            (200, b'{"choices":[{"message":{"content":"invalid"}}]}', None),
            (200, b"{}", OSError("fixture-only-private-value")),
        ]
        for status, payload, transport_error in cases:
            with self.subTest(status=status, payload=payload):
                model = adapter()
                response = Mock(status=status)
                response.read.return_value = payload
                connection = Mock()
                connection.getresponse.return_value = response
                connection.request.side_effect = transport_error
                with (
                    patch(
                        "neurolab.providers.http.client.HTTPSConnection", return_value=connection
                    ),
                    self.assertRaises(ModelProviderError) as raised,
                ):
                    model.generate_structured(MESSAGES, SCHEMA, timeout=1)
                self.assertNotIn("private", str(raised.exception))
                self.assertGreater(model.tokens_reserved, 0)
                connection.close.assert_called_once()

    def test_environment_validation_and_independent_refinement_output_budget(self):
        valid = {
            "MODEL_PROVIDER": "meta",
            "META_MODEL_API_BASE_URL": "https://provider.invalid/chat",
            "META_MODEL_API_KEY": "fixture",
            "META_MODEL_ID": "fixture",
            "META_MODEL_VERIFIED": "true",
        }
        with patch.dict(os.environ, valid, clear=True):
            model = OpenAICompatibleAdapter.from_environment()
            self.assertTrue(adapter_status()["enabled_for_runs"])
            with patch.object(model, "_request_structured", return_value={}) as request:
                model.generate_refinement(MESSAGES, SCHEMA, timeout=3)
            self.assertEqual(request.call_args.kwargs["max_tokens"], 2000)
        invalid = [
            {"MODEL_PROVIDER": "unsupported"},
            {"META_MODEL_API_BASE_URL": "http://provider.invalid"},
            {"MODEL_MAX_OUTPUT_TOKENS": "invalid"},
            {"MODEL_MAX_OUTPUT_TOKENS": "1"},
            {"MODEL_MAX_RUN_TOKENS": "invalid"},
            {"MODEL_MAX_RUN_TOKENS": "100001"},
            {"MODEL_MAX_CONTEXT_TOKENS": "invalid"},
            {"MODEL_MAX_CONTEXT_TOKENS": "1000"},
        ]
        for change in invalid:
            with (
                self.subTest(change=change),
                patch.dict(os.environ, {**valid, **change}, clear=True),
                self.assertRaises(ModelProviderError),
            ):
                OpenAICompatibleAdapter.from_environment()
        with patch.dict(
            os.environ,
            {"MODEL_MAX_RUN_TOKENS": "invalid", "MODEL_MAX_CONTEXT_TOKENS": "invalid"},
            clear=True,
        ):
            status = adapter_status()
        self.assertIsNone(status["max_run_tokens"])
        self.assertIsNone(status["max_context_tokens"])
