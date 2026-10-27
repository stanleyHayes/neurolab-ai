import json
import os
import sys
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from neurolab.agent import AgentConfigurationError, ResearchAgent  # noqa: E402
from neurolab.auth import (  # noqa: E402
    AuthenticationError,
    decode_access_token,
    hash_password,
    issue_access_token,
    keyed_hash,
    new_csrf_token,
    new_refresh_token,
    new_session_expiry,
    verify_keyed_hash,
    verify_password,
)
from neurolab.ghana import load_ghana  # noqa: E402
from neurolab.providers import (  # noqa: E402
    ModelProviderError,
    OpenAICompatibleAdapter,
    adapter_status,
)
from neurolab.store import RunStore  # noqa: E402
from neurolab.tools import (  # noqa: E402
    REGISTRY,
    ToolValidationError,
    execute_tool,
    validate_tool_call,
)

LOGIN_TEST_PASSWORD = "correct-horse-battery"  # noqa: S105 - deterministic test fixture


def valid_call(action="dataset_profile", parameters=None):
    return {
        "trace_id": "trace-test",
        "hypothesis_id": "hypothesis-test",
        "dataset_id": "ghana_combined",
        "action": action,
        "parameters": parameters or {},
    }


class ToolRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def test_valid_tool_returns_provenance_result_contract(self):
        result = execute_tool(valid_call(), self.dataset, seed=1)
        self.assertEqual(result["source_sha256"], self.dataset.source_sha256)
        self.assertEqual(result["tool_name"], "dataset_profile")
        self.assertEqual(result["sample_size"], 864)
        self.assertEqual(result["claim_scope"], "descriptive")

    def test_every_registered_tool_matches_result_schema(self):
        schema = json.loads((ROOT / "schemas/research_result.schema.json").read_text())
        validator = Draft202012Validator(schema)
        for action in REGISTRY:
            with self.subTest(action=action):
                result = execute_tool(
                    valid_call(action), self.dataset, seed=77, artifact_id=f"schema-{action}"
                )
                validator.validate(result)

    def test_unknown_action_and_extra_fields_rejected(self):
        forbidden_call = valid_call(action="execute_python")
        with self.assertRaises(ToolValidationError):
            validate_tool_call(forbidden_call)
        malformed = valid_call()
        malformed["extra"] = "not allowed"
        with self.assertRaises(ToolValidationError):
            validate_tool_call(malformed)

    def test_unimplemented_dataset_and_excessive_parameters_rejected(self):
        unsupported = valid_call()
        unsupported["dataset_id"] = "iita_full_irrigation"
        with self.assertRaises(ToolValidationError):
            validate_tool_call(unsupported)
        too_many = valid_call("compare_regimes", {"bootstrap_samples": 10001})
        with self.assertRaises(ToolValidationError):
            validate_tool_call(too_many)


class RunOrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana(ROOT)

    def setUp(self):
        self.store = RunStore(":memory:")

    def tearDown(self):
        self.store.close()

    def test_closed_loop_decisions_follow_computed_evidence(self):
        from neurolab.research_context import ResearchConfiguration

        # Pin the legacy three-method contract: this tests trace/evidence behavior,
        # independently of the automatic objective-routing policy.
        config = ResearchConfiguration(
            preferred_methods=[
                "block_bootstrap_contrast",
                "genotype_ranking",
                "missingness_audit",
            ]
        )
        result = ResearchAgent(
            self.dataset,
            self.store,
            configuration=config,
            max_steps=3,
            max_tool_calls=4,
            max_wall_time=30,
        ).run("Which genotypes warrant drought follow-up?", seed=81)
        report = result["report"]
        self.assertEqual(report["mode"], "deterministic_replay")
        self.assertIn("no model call", report["replay_label"])
        self.assertGreaterEqual(len(report["decisions"]), 2)
        self.assertEqual(len(report["evidence_ids"]), 3)
        second_decision = report["decisions"][1]
        second_evidence = next(
            artifact
            for artifact in self.store.list_artifacts(report["run_id"])
            if artifact["artifact_id"] == second_decision["based_on_evidence_id"]
        )
        measured_top_coverage = second_evidence["results"]["genotypes"][0]["environment_count"]
        expected_action = "inspect_missingness" if measured_top_coverage >= 3 else "dataset_profile"
        self.assertEqual(second_decision["selected_action"], expected_action)
        events = result["events"]
        self.assertEqual([event["sequence"] for event in events], list(range(1, len(events) + 1)))
        self.assertEqual(events[-1]["event_type"], "run.completed")
        evidence_ids = set(report["evidence_ids"])
        for decision in report["decisions"]:
            self.assertIn(decision["based_on_evidence_id"], evidence_ids)
        self.assertEqual(len(self.store.list_artifacts(report["run_id"])), 3)

    def test_live_meta_is_blocked_without_real_adapter(self):
        agent = ResearchAgent(self.dataset, self.store, mode="meta")
        with self.assertRaises(AgentConfigurationError):
            agent.run("test")

    def test_meta_loop_uses_structured_allowlisted_evidence_dependent_decisions(self):
        class FakeAdapter:
            provider = "test-fixture"
            model_id = "fixture-model"

            def __init__(self):
                self.calls = []

            def generate_structured(self, messages, schema, *, timeout):
                self.calls.append(messages)
                return {
                    "action": "compare_regimes" if len(self.calls) == 1 else "rank_genotypes",
                    "bootstrap_samples": 200 if len(self.calls) == 1 else None,
                    "decision_summary": "Choose a bounded analysis relevant to the objective.",
                }

        adapter = FakeAdapter()
        result = ResearchAgent(
            self.dataset,
            self.store,
            max_steps=3,
            max_tool_calls=4,
            mode="meta",
            model_adapter=adapter,
        ).run("Check observed yield and genotype patterns", seed=8)
        report = result["report"]
        self.assertEqual(report["mode"], "meta")
        self.assertEqual(report["model_provider"], "test-fixture")
        self.assertEqual(len(adapter.calls), 3)
        self.assertEqual(report["source_sha256"], self.dataset.source_sha256)
        self.assertIn('"artifact_id":"', adapter.calls[1][1]["content"])
        self.assertEqual(len(report["evidence_ids"]), 3)
        self.assertEqual(len(report["grounded_claims"]), 3)
        for claim in report["grounded_claims"]:
            self.assertIn(claim["evidence_ids"][0], report["evidence_ids"])
        for decision in report["decisions"][1:]:
            self.assertIn(decision["based_on_evidence_id"], report["evidence_ids"])
        self.assertEqual(report["decisions"][0]["selection_source"], "model")
        self.assertTrue(
            all(
                item["source_sha256"] == self.dataset.source_sha256
                for item in self.store.list_artifacts(report["run_id"])
            )
        )

    def test_meta_invalid_action_is_rejected_and_safely_recovered(self):
        class InvalidOnceAdapter:
            provider = "test-fixture"
            model_id = "fixture-model"

            def __init__(self):
                self.calls = 0

            def generate_structured(self, messages, schema, *, timeout):
                self.calls += 1
                action = "execute_shell" if self.calls == 1 else "dataset_profile"
                return {
                    "action": action,
                    "bootstrap_samples": None,
                    "decision_summary": "Use a bounded descriptive analysis.",
                }

        result = ResearchAgent(
            self.dataset, self.store, max_steps=2, mode="meta", model_adapter=InvalidOnceAdapter()
        ).run("test")
        self.assertTrue(any(event["event_type"] == "decision.failed" for event in result["events"]))
        self.assertTrue(result["report"]["tool_failures"])
        artifacts = self.store.list_artifacts(result["report"]["run_id"])
        self.assertEqual(
            [item["tool_name"] for item in artifacts], ["compare_regimes", "rank_genotypes"]
        )
        self.assertEqual(result["run"]["status"], "PARTIAL")
        self.assertEqual(result["events"][-1]["event_type"], "run.partial")

    def test_provider_requires_verified_runtime_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(adapter_status()["enabled_for_runs"])
            with self.assertRaises(ModelProviderError):
                OpenAICompatibleAdapter.from_environment()

    def test_provider_reserves_and_enforces_per_run_token_budget(self):
        adapter = OpenAICompatibleAdapter(
            endpoint="https://provider.invalid/chat/completions",
            api_key="not-a-real-secret",
            model_id="fixture",
            max_output_tokens=100,
            max_run_tokens=200,
        )
        with self.assertRaisesRegex(ModelProviderError, "token budget exhausted"):
            adapter.generate_structured(
                [{"role": "user", "content": "x" * 500}],
                {"type": "object"},
                timeout=1,
            )
        self.assertEqual(adapter.tokens_reserved, 0)

    def test_cancellation_is_persisted_and_run_exits_at_safe_boundary(self):
        run_id = self.store.create_run(
            "ghana_combined", "cancel test", self.dataset.source_sha256, 9
        )
        self.store.request_cancel(run_id)
        result = ResearchAgent(self.dataset, self.store, mode="replay").run(
            "cancel test", run_id=run_id
        )
        self.assertIsNone(result["report"])
        self.assertEqual(result["run"]["status"], "CANCELLED")
        self.assertEqual(result["events"][-1]["event_type"], "run.cancelled")

    def test_failed_tool_records_error_and_executes_bounded_recovery(self):
        from neurolab import agent as agent_module

        original = agent_module.execute_tool

        def fail_contrast_once(call, dataset, **kwargs):
            if call["action"] == "compare_regimes":
                raise RuntimeError("injected transient failure")
            return original(call, dataset, **kwargs)

        with patch("neurolab.agent.execute_tool", side_effect=fail_contrast_once):
            result = ResearchAgent(self.dataset, self.store, max_steps=3, max_tool_calls=4).run(
                "Exercise recovery", seed=77
            )
        events = result["events"]
        self.assertTrue(any(event["event_type"] == "tool.failed" for event in events))
        recovery = next(
            event
            for event in events
            if event["event_type"] == "tool.requested" and "recovery_for" in event["payload"]
        )
        self.assertEqual(recovery["payload"]["action"], "dataset_profile")
        self.assertEqual(result["report"]["tool_calls"], 2)
        self.assertEqual(result["report"]["completion_status"], "partial")
        self.assertTrue(result["report"]["tool_failures"][0]["recovered"])
        self.assertEqual(len(self.store.list_artifacts(result["report"]["run_id"])), 1)

    def test_budget_caps_enforced(self):
        with self.assertRaises(ValueError):
            ResearchAgent(self.dataset, self.store, max_steps=7)


class AuthenticationPrimitiveTests(unittest.TestCase):
    def test_argon2_password_hash_validation_and_mismatch(self):
        password = "correct-horse-battery-staple"  # noqa: S105 - deterministic test fixture
        encoded = hash_password(password)
        self.assertTrue(encoded.startswith("$argon2id$"))
        self.assertTrue(verify_password(encoded, password))
        self.assertFalse(verify_password(encoded, "incorrect-password"))
        with self.assertRaises(ValueError):
            hash_password("short")

    def test_ed25519_token_claims_and_rejects_tampering_wrong_kid_and_alg(self):
        from neurolab.auth import _cached_key_material

        _cached_key_material.cache_clear()
        token = issue_access_token("opaque-user-id", "session-id")
        claims = decode_access_token(token)
        self.assertEqual(claims["sub"], "opaque-user-id")
        self.assertEqual(claims["sid"], "session-id")
        self.assertEqual(claims["token_type"], "access")
        self.assertEqual(claims["exp"] - claims["iat"], 720)
        parts = token.split(".")
        tampered_signature = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        tampered = f"{parts[0]}.{parts[1]}.{tampered_signature}"
        with self.assertRaises(AuthenticationError):
            decode_access_token(tampered)
        import jwt

        untrusted_header = jwt.get_unverified_header(token)
        self.assertEqual(untrusted_header["alg"], "EdDSA")
        self.assertEqual(untrusted_header["kid"], "local-ed25519-v1")

    def test_token_hash_is_keyed_and_refresh_values_are_random(self):
        first = new_refresh_token()
        second = new_refresh_token()
        self.assertNotEqual(first, second)
        hashed = keyed_hash(first)
        self.assertNotEqual(first, hashed)
        self.assertTrue(verify_keyed_hash(first, hashed))
        self.assertFalse(verify_keyed_hash(second, hashed))
        first_csrf = new_csrf_token()
        second_csrf = new_csrf_token()
        self.assertNotEqual(first_csrf, second_csrf)

    def test_jwt_rejects_wrong_key_id_algorithm_issuer_audience_type_and_expiry(self):
        import jwt

        from neurolab.auth import AUDIENCE, ISSUER, _key_material

        private_key, public_key, kid = _key_material()
        now = datetime.now(UTC)
        valid = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "user",
            "sid": "session",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=2)).timestamp()),
            "jti": str(uuid.uuid4()),
            "token_type": "access",
        }
        for case, claims, header, algorithm in (
            ("kid", valid, {"kid": "unknown", "typ": "JWT"}, "EdDSA"),
            (
                "issuer",
                {**valid, "iss": "https://untrusted.invalid"},
                {"kid": kid, "typ": "JWT"},
                "EdDSA",
            ),
            ("audience", {**valid, "aud": "other"}, {"kid": kid, "typ": "JWT"}, "EdDSA"),
            ("type", {**valid, "token_type": "refresh"}, {"kid": kid, "typ": "JWT"}, "EdDSA"),
            (
                "expired",
                {**valid, "exp": int((now - timedelta(minutes=1)).timestamp())},
                {"kid": kid, "typ": "JWT"},
                "EdDSA",
            ),
            (
                "not-before",
                {**valid, "nbf": int((now + timedelta(hours=1)).timestamp())},
                {"kid": kid, "typ": "JWT"},
                "EdDSA",
            ),
            ("algorithm", valid, {"kid": kid, "typ": "JWT"}, "HS256"),
        ):
            with self.subTest(case=case):
                secret = "not-an-ed25519-key" if algorithm == "HS256" else private_key
                token = jwt.encode(claims, secret, algorithm=algorithm, headers=header)
                with self.assertRaises(AuthenticationError):
                    decode_access_token(token)


class AuthSessionStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = RunStore(":memory:")
        self.user = self.store.create_user("owner@example.test", "argon-hash", "Owner")
        self.refresh = new_refresh_token()
        self.csrf = new_csrf_token()
        self.session_id = "session-one"
        self.family_id = "family-one"
        self.store.create_auth_session(
            session_id=self.session_id,
            user_id=self.user["user_id"],
            refresh_token_hash=keyed_hash(self.refresh),
            csrf_token_hash=keyed_hash(self.csrf),
            family_id=self.family_id,
            expires_at=new_session_expiry(),
        )

    def tearDown(self):
        self.store.close()

    def test_rotation_and_reuse_revokes_descendant_family(self):
        new_refresh = new_refresh_token()
        state, rotated = self.store.rotate_auth_session(
            old_refresh_hash=keyed_hash(self.refresh),
            new_session_id="session-two",
            new_refresh_hash=keyed_hash(new_refresh),
            new_csrf_hash=keyed_hash(new_csrf_token()),
            new_expires_at=new_session_expiry(),
            now=self.store._now(),
        )
        self.assertEqual(state, "rotated")
        self.assertEqual(rotated["session_id"], "session-two")
        self.assertTrue(
            self.store.get_active_auth_session(
                "session-two", self.user["user_id"], self.store._now()
            )
        )
        replay_state, replay = self.store.rotate_auth_session(
            old_refresh_hash=keyed_hash(self.refresh),
            new_session_id="session-three",
            new_refresh_hash=keyed_hash(new_refresh_token()),
            new_csrf_hash=keyed_hash(new_csrf_token()),
            new_expires_at=new_session_expiry(),
            now=self.store._now(),
        )
        self.assertEqual((replay_state, replay), ("reuse", None))
        self.assertFalse(
            self.store.get_active_auth_session(
                "session-two", self.user["user_id"], self.store._now()
            )
        )

    def test_owned_run_query_hides_other_owners_and_unowned_legacy(self):

        run_id = self.store.create_run("ghana_combined", "private", "hash", 3, self.user["user_id"])
        other = self.store.create_user("other@example.test", "argon-hash", "Other")
        self.assertEqual(len(self.store.list_runs(owner_user_id=self.user["user_id"])), 1)
        self.assertIsNone(self.store.get_run(run_id, owner_user_id=other["user_id"]))
        self.assertEqual(self.store.list_runs(owner_user_id=other["user_id"]), [])
        legacy = self.store.create_run("ghana_combined", "quarantined", "hash", 4)
        self.assertIsNone(self.store.get_run(legacy, owner_user_id=self.user["user_id"]))
        self.assertIsNotNone(self.store.get_run(legacy))


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "sqlite:///:memory:",
                "APP_ENV": "test",
                "AUTH_INVITE_CODE": "test-invite",
            },
            clear=True,
        ):
            from fastapi.testclient import TestClient

            from neurolab.api import app

            cls.client = TestClient(app)

    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "DATABASE_URL": "sqlite:///:memory:",
                "APP_ENV": "test",
                "AUTH_INVITE_CODE": "test-invite",
            },
            clear=True,
        )
        self.environment.start()
        from neurolab.api import STORE

        STORE.close()
        STORE.reopen()
        from fastapi.testclient import TestClient

        from neurolab.api import app

        self.client = TestClient(app, client=(f"fixture-{self._testMethodName}", 50000))
        self.client.cookies.clear()
        self.client.headers.clear()
        self.client.get("/auth/csrf")
        self.client.headers["x-csrf-token"] = self.csrf

    def test_credit_pause_blocks_meta_run_and_refinement_before_network_or_run_creation(self):
        self.register("paused@example.test")
        with (
            patch.dict(
                os.environ,
                {
                    "MODEL_PROVIDER": "meta",
                    "META_MODEL_API_BASE_URL": "https://provider.invalid/chat",
                    "META_MODEL_API_KEY": "fixture",
                    "META_MODEL_ID": "fixture",
                    "META_MODEL_VERIFIED": "true",
                    "MODEL_INFERENCE_ENABLED": "false",
                },
            ),
            patch("neurolab.api.OpenAICompatibleAdapter.from_environment") as adapter,
        ):
            run = self.client.post(
                "/research-runs", json={"objective": "Credit pause acceptance", "mode": "meta"}
            )
            refined = self.client.post(
                "/research-objectives/refine",
                json={"objective": "Credit pause acceptance", "configuration": {}},
            )
            capabilities = self.client.get("/research-capabilities")
            self.assertFalse(capabilities.json()["model_inference_enabled"])
            self.assertTrue(capabilities.json()["drafts_available"])
            self.assertNotIn("fixture", capabilities.text)
            self.assertEqual(run.status_code, 503)
            self.assertEqual(refined.status_code, 503)
            adapter.assert_not_called()
            self.assertEqual(self.client.get("/research-runs").json(), [])

    def test_full_investigation_api_and_invalid_profile_plan_are_owner_scoped_and_model_free(self):
        self.register("investigation@example.test")
        objective = (ROOT / "tests/fixtures/ghana-research-objective.txt").read_text()
        configuration = {
            "desired_outputs": ["ghana_drought_investigation"],
            "constraints": {"max_steps": 6, "max_tool_calls": 6, "max_seconds": 180},
        }
        with (
            patch.dict(os.environ, {"MODEL_INFERENCE_ENABLED": "false"}),
            patch("neurolab.api.OpenAICompatibleAdapter.from_environment") as adapter,
        ):
            created = self.client.post(
                "/research-runs",
                json={"objective": objective, "mode": "replay", "configuration": configuration},
            )
            self.assertEqual(created.status_code, 202)
            run_id = created.json()["run_id"]
            saved = self.client.get(f"/research-runs/{run_id}").json()
            self.assertEqual(saved["status"], "COMPLETE")
            self.assertEqual(saved["report"]["objective"], objective)
            self.assertEqual(len(saved["report"]["scientific_report"]["hypothesis_evaluations"]), 4)
            self.assertEqual(len(self.client.get(f"/research-runs/{run_id}/artifacts").json()), 6)
            from neurolab.research_context import ResearchConfiguration, build_deterministic_plan

            incompatible = build_deterministic_plan(objective, ResearchConfiguration()).model_dump(
                mode="json"
            )
            rejected = self.client.post(
                "/research-runs",
                json={
                    "objective": objective,
                    "mode": "replay",
                    "configuration": configuration,
                    "plan": incompatible,
                },
            )
            self.assertEqual(rejected.status_code, 409)
            invalid = self.client.post(
                "/research-runs",
                json={
                    "objective": objective,
                    "configuration": {**configuration, "preferred_methods": ["dataset_profile"]},
                },
            )
            self.assertEqual(invalid.status_code, 422)
            fixed = self.client.post(
                "/research-objectives/refine",
                json={"objective": objective, "configuration": configuration},
            )
            self.assertEqual(fixed.status_code, 422)
            adapter.assert_not_called()
            self.assertEqual(len(self.client.get("/research-runs").json()), 1)

    @property
    def csrf(self):
        return self.client.cookies.get("neurolab_csrf", "")

    def register(self, email, password=None, display_name="Researcher"):
        password = password or LOGIN_TEST_PASSWORD
        self.client.get("/auth/csrf")
        self.client.headers["x-csrf-token"] = self.csrf
        response = self.client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "display_name": display_name,
                "invite_code": "test-invite",
            },
        )
        if response.status_code == 201:
            self.authenticate(response.json()["access_token"])
        return response

    def authenticate(self, token):
        self.client.headers["authorization"] = f"Bearer {token}"
        self.client.headers["x-csrf-token"] = self.csrf

    def login(self, email, password=None):
        self.client.headers.pop("authorization", None)
        return self.client.post(
            "/auth/login",
            json={"email": email, "password": password or LOGIN_TEST_PASSWORD},
        )

    def tearDown(self):
        self.environment.stop()

    def test_long_objectives_survive_draft_persistence_and_actual_run_execution(self):
        self.register(f"long-{uuid.uuid4()}@example.test")
        revision = 0
        for size in (40, 5_000, 20_000):
            with self.subTest(characters=size):
                base = "# Research objective\r\n\nPreserve λ, paragraphs and **Markdown**.\n"
                objective = (base * (size // len(base) + 1))[:size]
                config = {
                    "preferred_methods": ["dataset_profile"],
                    "constraints": {"max_steps": 1, "max_tool_calls": 1, "max_seconds": 30},
                }
                saved = self.client.put(
                    "/research-draft",
                    json={
                        "expected_revision": revision,
                        "draft": {"objective": objective, **config},
                    },
                )
                self.assertEqual(saved.status_code, 200, saved.text)
                revision = saved.json()["revision"]
                self.assertEqual(
                    self.client.get("/research-draft").json()["draft"]["objective"], objective
                )
                accepted = self.client.post(
                    "/research-runs", json={"objective": objective, "configuration": config}
                )
                self.assertEqual(accepted.status_code, 202, accepted.text)
                run = self.client.get("/research-runs/" + accepted.json()["run_id"]).json()
                self.assertEqual(run["status"], "COMPLETE")
                self.assertEqual(run["objective"], objective)
                self.assertEqual(run["report"]["objective"], objective)
                self.assertEqual(run["report"]["research_plan"]["tasks"][0]["status"], "completed")
                self.assertEqual(run["report"]["tool_calls"], 1)

    def test_drafts_are_owner_scoped_and_stale_revision_cannot_overwrite(self):
        first = self.register(f"draft-a-{uuid.uuid4()}@example.test").json()["access_token"]
        original = "Private first-owner objective\n<script>alert('test')</script>"
        self.assertEqual(
            self.client.put(
                "/research-draft", json={"expected_revision": 0, "draft": {"objective": original}}
            ).status_code,
            200,
        )
        self.register(f"draft-b-{uuid.uuid4()}@example.test")
        self.assertEqual(self.client.get("/research-draft").json()["revision"], 0)
        invalid = self.client.put(
            "/research-draft",
            json={
                "expected_revision": 0,
                "owner_user_id": "forged",
                "draft": {"objective": "Other"},
            },
        )
        self.assertEqual(invalid.status_code, 422)
        self.authenticate(first)
        self.assertEqual(self.client.get("/research-draft").json()["draft"]["objective"], original)
        updated = self.client.put(
            "/research-draft", json={"expected_revision": 1, "draft": {"objective": "New revision"}}
        )
        self.assertEqual(updated.status_code, 200)
        stale = self.client.put(
            "/research-draft",
            json={"expected_revision": 1, "draft": {"objective": "Stale overwrite"}},
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(
            self.client.get("/research-draft").json()["draft"]["objective"], "New revision"
        )

    def test_oversized_objective_is_rejected_without_replacing_saved_draft(self):
        self.register(f"draft-size-{uuid.uuid4()}@example.test")
        valid = {"expected_revision": 0, "draft": {"objective": "Kept draft"}}
        self.assertEqual(self.client.put("/research-draft", json=valid).status_code, 200)
        invalid = {"expected_revision": 1, "draft": {"objective": "λ" * 20_001}}
        self.assertEqual(self.client.put("/research-draft", json=invalid).status_code, 422)
        self.assertEqual(
            self.client.get("/research-draft").json()["draft"]["objective"], "Kept draft"
        )
        self.assertEqual(
            self.client.post("/research-runs", json={"objective": "λ" * 20_001}).status_code, 422
        )

    def test_refinement_and_automatic_planning_use_validated_fixture_contracts(self):
        from unittest.mock import Mock

        from neurolab.research_context import ResearchConfiguration, build_deterministic_plan

        self.register(f"refine-{uuid.uuid4()}@example.test")
        original = "# Full original\n\n" + "λ" * 5000
        config = ResearchConfiguration(preferred_methods=["dataset_profile"])
        proposed = build_deterministic_plan(original, config).model_dump(mode="json")
        for key in ("planning_mode", "objective_sha256"):
            proposed.pop(key)
        for task in proposed["tasks"]:
            task.pop("status")
            task.pop("evidence_ids")
        for suggestion in proposed["dataset_suggestions"]:
            suggestion.pop("enabled_for_analysis")
        proposed["important_constraints"] = ["Never pool unrelated experiments"]
        adapter = Mock(provider="test-fixture", model_id="not-live-inference")
        adapter.generate_refinement.return_value = proposed
        adapter.generate_structured.return_value = {
            "action": "dataset_profile",
            "bootstrap_samples": None,
            "decision_summary": "Inspect the supported source",
        }
        with (
            patch("neurolab.api.adapter_status", return_value={"enabled_for_runs": True}),
            patch("neurolab.api.OpenAICompatibleAdapter.from_environment", return_value=adapter),
        ):
            refined = self.client.post(
                "/research-objectives/refine",
                json={"objective": original, "configuration": config.model_dump(mode="json")},
            )
            self.assertEqual(refined.status_code, 200, refined.text)
            self.assertEqual(refined.json()["original_objective"], original)
            accepted = self.client.post(
                "/research-runs",
                json={
                    "objective": original,
                    "mode": "meta",
                    "configuration": config.model_dump(mode="json"),
                },
            )
        run = self.client.get("/research-runs/" + accepted.json()["run_id"]).json()
        self.assertEqual(run["status"], "COMPLETE")
        self.assertEqual(run["report"]["objective"], original)
        self.assertEqual(run["report"]["tool_calls"], 1)
        self.assertEqual(
            run["report"]["research_plan"]["important_constraints"],
            proposed["important_constraints"],
        )
        self.assertEqual(run["report"]["research_plan"]["tasks"][0]["status"], "completed")
        context = json.loads(adapter.generate_structured.call_args.args[0][1]["content"])
        self.assertIsNone(context["objective"])
        self.assertEqual(
            context["context"]["important_constraints"], proposed["important_constraints"]
        )

    def test_dataset_requires_user_and_profile_is_readable(self):
        self.assertEqual(self.client.get("/datasets").status_code, 401)
        user = self.register(f"profile-{uuid.uuid4()}@example.test")
        self.assertEqual(user.status_code, 201)
        profile = self.client.get("/datasets/ghana_combined/profile")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["row_count"], 864)

    def test_durable_queue_survives_http_without_inline_execution_and_cancel_is_owner_scoped(self):
        self.register(f"queued-{uuid.uuid4()}@example.test")
        with patch.dict(os.environ, {"RESEARCH_INLINE_WORKER": "false"}):
            response = self.client.post("/research-runs", json={"objective": "Profile the source."})
        self.assertEqual(response.status_code, 202)
        rid = response.json()["run_id"]
        self.assertEqual(self.client.get(f"/research-runs/{rid}").json()["status"], "QUEUED")
        status = self.client.get(f"/research-runs/{rid}/job")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["state"], "QUEUED")
        self.assertNotIn("claim_token", status.json())
        self.assertEqual(self.client.post(f"/research-runs/{rid}/cancel").status_code, 202)
        self.assertEqual(self.client.get(f"/research-runs/{rid}").json()["status"], "CANCELLED")
        self.assertEqual(self.client.get(f"/research-runs/{rid}/job").json()["state"], "CANCELLED")

    def test_account_analysis_limits_hold_across_peers_without_consuming_other_accounts(self):
        from fastapi.testclient import TestClient

        from neurolab.api import STORE, app, execute_tool

        self.register(f"rate-owner-{uuid.uuid4()}@example.test")
        clients = [TestClient(app, client=(ip, 5000)) for ip in ("198.51.100.11", "198.51.100.12")]
        for client in clients:
            client.headers.update(dict(self.client.headers))
        payload = valid_call()
        with (
            patch.object(STORE, "database_epoch", return_value=120),
            patch("neurolab.api.execute_tool", wraps=execute_tool) as tool,
        ):
            for index in range(10):
                response = clients[index % 2].post("/research-tools/execute", json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["results"]["row_count"], 864)
            denied = clients[1].post("/research-tools/execute", json=payload)
            self.assertEqual(denied.status_code, 429)
            self.assertEqual(denied.headers["retry-after"], "60")
            self.assertEqual(tool.call_count, 10)
            self.assertEqual(clients[0].get("/datasets").status_code, 200)
        for client in clients:
            client.close()

    def test_refresh_rotation_has_a_shared_verified_owner_budget(self):
        from neurolab.api import STORE
        from neurolab.rate_limits import SharedRateLimiter

        account = self.register(f"refresh-rate-{uuid.uuid4()}@example.test").json()["user"]
        with patch.object(STORE, "database_epoch", return_value=120):
            limiter = SharedRateLimiter(STORE)
            for _ in range(29):
                limiter.consume(account["user_id"], "account:refresh", 30)

            # Browser cookies target /api/auth at the BFF; a direct FastAPI
            # test must explicitly relay that same cookie/CSRF pair.
            def cookie():
                return (
                    f"neurolab_refresh={self.client.cookies.get('neurolab_refresh')}; "
                    f"neurolab_csrf={self.csrf}"
                )

            first = self.client.post(
                "/auth/refresh", headers={"cookie": cookie(), "x-csrf-token": self.csrf}
            )
            self.assertEqual(first.status_code, 200, first.text)
            denied = self.client.post(
                "/auth/refresh", headers={"cookie": cookie(), "x-csrf-token": self.csrf}
            )
            self.assertEqual(denied.status_code, 429)
            self.assertEqual(denied.headers["retry-after"], "60")
            self.authenticate(first.json()["access_token"])
            self.assertEqual(self.client.get("/auth/me").status_code, 200)

    def test_invalid_access_token_cannot_allocate_a_claimed_account_bucket(self):
        from neurolab.api import STORE

        owner = self.register(f"invalid-rate-{uuid.uuid4()}@example.test").json()["user"]
        self.client.headers["authorization"] = "Bearer invalid-signature"
        self.assertEqual(self.client.get("/datasets").status_code, 401)
        key = keyed_hash("rate:v1:account:all:" + owner["user_id"])
        with STORE._lock:
            count = STORE._execute(
                "SELECT COUNT(*) AS n FROM request_rate_buckets WHERE bucket_key=?", (key,)
            ).fetchone()["n"]
        self.assertEqual(count, 0)

    def test_cross_user_run_resources_are_isolated(self):
        first = self.register(f"first-{uuid.uuid4()}@example.test")
        created = self.client.post("/research-runs", json={"objective": "private owner run"})
        self.assertEqual(created.status_code, 202)
        run_id = created.json()["run_id"]
        second = self.register(f"second-{uuid.uuid4()}@example.test", display_name="Second")
        self.assertEqual(second.status_code, 201)
        self.assertEqual(self.client.get("/research-runs").json(), [])
        for suffix in ("", "/events", "/artifacts", "/report", "/bundle", "/job"):
            with self.subTest(resource=suffix):
                self.assertEqual(
                    self.client.get(f"/research-runs/{run_id}{suffix}").status_code, 404
                )
        self.assertEqual(self.client.post(f"/research-runs/{run_id}/cancel").status_code, 404)
        self.authenticate(first.json()["access_token"])
        self.assertEqual(self.client.get(f"/research-runs/{run_id}").status_code, 200)
        bundle = self.client.get(f"/research-runs/{run_id}/bundle")
        self.assertEqual(bundle.status_code, 200)
        self.assertEqual(set(bundle.json()), {"bundle_version", "report", "artifacts", "events"})
        self.assertEqual(bundle.json()["report"]["run_id"], run_id)
        self.assertEqual(len(bundle.json()["artifacts"]), 3)
        self.assertEqual(bundle.json()["events"][-1]["event_type"], "run.completed")
        self.assertIn(
            "event: run.completed", self.client.get(f"/research-runs/{run_id}/events").text
        )

    def test_invite_gate_email_uniqueness_rotation_and_logout(self):
        denied = self.client.post(
            "/auth/register",
            json={
                "email": "closed@example.test",
                "password": "correct-horse-battery",
                "display_name": "Closed",
            },
        )
        self.assertEqual(denied.status_code, 403)
        created = self.register(f"rotate-{uuid.uuid4()}@example.test")
        email = created.json()["user"]["email"]
        duplicate = self.client.post(
            "/auth/register",
            json={
                "email": email.upper(),
                "password": "another-secure-password",
                "display_name": "Duplicate",
                "invite_code": "test-invite",
            },
        )
        self.assertEqual(duplicate.status_code, 409)
        old_refresh, old_csrf = self.client.cookies.get("neurolab_refresh"), self.csrf
        wrong = self.client.post(
            "/auth/refresh",
            headers={
                "x-csrf-token": "wrong",
                "cookie": f"neurolab_refresh={old_refresh}; neurolab_csrf={old_csrf}",
            },
        )
        self.assertEqual(wrong.status_code, 403)
        rotated = self.client.post(
            "/auth/refresh",
            headers={
                "x-csrf-token": old_csrf,
                "cookie": f"neurolab_refresh={old_refresh}; neurolab_csrf={old_csrf}",
            },
        )
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(self.client.cookies.get("neurolab_refresh"), old_refresh)
        self.authenticate(rotated.json()["access_token"])
        changed = self.client.post(
            "/auth/change-password",
            json={
                "current_password": "correct-horse-battery",
                "new_password": "brand-new-secure-passphrase",
            },
        )
        self.assertEqual(changed.status_code, 204)
        self.assertEqual(self.client.post("/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

    def test_login_lockout_escalates_and_success_clears_failures(self):
        email = f"lockout-{uuid.uuid4()}@example.test"
        self.assertEqual(self.register(email).status_code, 201)

        for _ in range(5):
            failed = self.login(email, "incorrect-password")
            self.assertEqual(failed.status_code, 401)

        blocked = self.login(email)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.headers["retry-after"], "30")

        from neurolab.api import STORE
        from neurolab.auth import keyed_hash, session_now

        identifier_hash = keyed_hash(email.casefold())
        expired_at = (
            (datetime.fromisoformat(session_now().replace("Z", "+00:00")) - timedelta(seconds=1))
            .isoformat()
            .replace("+00:00", "Z")
        )
        with STORE.atomic():
            STORE._execute(
                "UPDATE auth_login_limits SET blocked_until = ? WHERE identifier_hash = ?",
                (expired_at, identifier_hash),
            )

        failed = self.login(email, "incorrect-password")
        self.assertEqual(failed.status_code, 401)
        escalated = self.login(email)
        self.assertEqual(escalated.status_code, 429)
        self.assertEqual(escalated.headers["retry-after"], "60")

        with STORE.atomic():
            STORE._execute(
                "UPDATE auth_login_limits SET blocked_until = ? WHERE identifier_hash = ?",
                (expired_at, identifier_hash),
            )
        succeeded = self.login(email)
        self.assertEqual(succeeded.status_code, 200)
        self.assertEqual(STORE.login_rate_limit_seconds(identifier_hash, session_now()), 0)
        self.assertEqual(
            STORE._execute(
                "SELECT COUNT(*) AS count FROM auth_login_limits WHERE identifier_hash = ?",
                (identifier_hash,),
            ).fetchone()["count"],
            0,
        )

    def test_run_events_report_artifacts_and_meta_gate(self):
        self.register(f"run-{uuid.uuid4()}@example.test")
        response = self.client.post(
            "/research-runs", json={"objective": "persisted owner run", "seed": 91}
        )
        self.assertEqual(response.status_code, 202)
        run_id = response.json()["run_id"]
        self.assertEqual(self.client.get(f"/research-runs/{run_id}").json()["status"], "COMPLETE")
        self.assertIn(
            "event: run.completed", self.client.get(f"/research-runs/{run_id}/events").text
        )
        self.assertEqual(len(self.client.get(f"/research-runs/{run_id}/artifacts").json()), 3)
        self.assertEqual(self.client.get(f"/research-runs/{run_id}/report").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/research-runs", json={"objective": "live", "mode": "meta"}
            ).status_code,
            503,
        )

    def test_body_limit_and_tool_validation(self):
        self.register(f"limit-{uuid.uuid4()}@example.test")
        oversized = self.client.post(
            "/research-runs",
            content=b" " * (256 * 1024 + 1),
            headers={"content-type": "application/json"},
        )
        self.assertEqual(oversized.status_code, 413)
        malformed = self.client.post(
            "/research-tools/execute",
            json={
                "trace_id": "t",
                "hypothesis_id": "h",
                "dataset_id": "ghana_combined",
                "action": "dataset_profile",
                "unexpected": True,
            },
        )
        self.assertNotEqual(malformed.status_code, 200)

    def test_production_service_auth_remains_separate(self):
        import subprocess

        key = (
            Ed25519PrivateKey.generate()
            .private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
            .decode()
        )
        program = "from fastapi.testclient import TestClient; from neurolab.api import app; c=TestClient(app); h={'host':'api.example.test','x-neurolab-service-token':'x'*32}; assert c.get('/health',headers=h).json()=={'status':'ok'}; assert c.get('/openapi.json',headers=h).status_code==404; assert c.get('/datasets',headers=h).status_code==401"
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "PYTHONPATH": str(ROOT),
            "APP_ENV": "production",
            "API_BEARER_TOKEN": "x" * 32,
            "ALLOWED_HOSTS": "api.example.test",
            "AUTH_ED25519_PRIVATE_KEY": key,
            "AUTH_TOKEN_PEPPER": "p" * 40,
            "AUTH_JWT_KID": "test-v1",
            "DATABASE_URL": "sqlite:///:memory:",
        }
        result = subprocess.run(  # noqa: S603 - fixed test interpreter and inline test program
            [sys.executable, "-c", program],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )  # noqa: S603
        self.assertEqual(result.returncode, 0, result.stderr)


class RequestSecurityMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def _request(self, middleware, *, path="/datasets", method="GET", headers=(), body=b""):
        messages = [{"type": "http.request", "body": body, "more_body": False}]
        sent = []

        async def receive():
            return messages.pop(0) if messages else {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": list(headers),
            "client": ("198.51.100.5", 1234),
            "server": ("test", 80),
        }
        await middleware(scope, receive, send)
        return sent[0]["status"], dict(sent[0].get("headers", []))

    async def test_authentication_and_rate_limits_are_enforced(self):
        from neurolab.api import RequestSecurityMiddleware

        async def ok_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        authenticated = RequestSecurityMiddleware(
            ok_app,
            bearer_token="a" * 32,
            require_auth=True,
            requests_per_minute=10,
        )
        status, headers = await self._request(authenticated)
        self.assertEqual(status, 401)
        status, _ = await self._request(
            authenticated,
            headers=[(b"x-neurolab-service-token", b"a" * 32)],
        )
        self.assertEqual(status, 204)

        expensive_limited = RequestSecurityMiddleware(
            ok_app,
            requests_per_minute=10,
            expensive_requests_per_minute=1,
        )
        self.assertEqual(
            (await self._request(expensive_limited, path="/research-runs", method="POST"))[0],
            204,
        )
        limited_status, limited_headers = await self._request(
            expensive_limited, path="/research-runs", method="POST"
        )
        self.assertEqual(limited_status, 429)
        self.assertGreaterEqual(int(limited_headers[b"retry-after"]), 1)
        self.assertLessEqual(int(limited_headers[b"retry-after"]), 60)

    async def test_chunked_body_limit_rejects_without_calling_app(self):
        from neurolab.api import RequestSecurityMiddleware

        calls = 0

        async def ok_app(scope, receive, send):
            nonlocal calls
            calls += 1

        middleware = RequestSecurityMiddleware(ok_app, max_body_bytes=4)
        messages = [
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": False},
        ]
        sent = []

        async def receive():
            return messages.pop(0)

        async def send(message):
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/research-runs",
            "headers": [],
            "client": ("198.51.100.8", 1234),
            "scheme": "http",
        }
        await middleware(scope, receive, send)
        self.assertEqual(sent[0]["status"], 413)
        self.assertEqual(calls, 0)


if __name__ == "__main__":
    unittest.main()
