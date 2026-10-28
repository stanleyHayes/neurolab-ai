"""Deployment profile admission and graceful queue draining; no provider requests."""

import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from neurolab.deployment_runtime import configure_deployment, configure_replay
from neurolab.provenance import git_revision
from neurolab.worker import poll_queue


class DeploymentRuntimeTests(unittest.TestCase):
    def test_meta_opt_in_requires_verified_pricing_and_preserves_worker_isolation(self):
        from tests.test_providers import SPEND_ENV

        settings = {
            **SPEND_ENV,
            "DATABASE_URL": "postgresql://example.invalid/research",
            "MODEL_INFERENCE_ENABLED": "true",
            "META_MODEL_API_KEY": "synthetic-test-secret",
            "META_MODEL_VERIFIED": "true",
            "AUTH_ED25519_PRIVATE_KEY": "synthetic-signing-key",
            "API_BEARER_TOKEN": "synthetic-service-secret",
        }
        with patch.dict(os.environ, settings, clear=True):
            configure_deployment(worker=True)
            self.assertEqual(os.environ["MODEL_INFERENCE_ENABLED"], "true")
            self.assertEqual(os.environ["META_MODEL_API_KEY"], "synthetic-test-secret")
            self.assertNotIn("AUTH_ED25519_PRIVATE_KEY", os.environ)
            self.assertNotIn("API_BEARER_TOKEN", os.environ)
            self.assertEqual(os.environ["RESEARCH_INLINE_WORKER"], "false")
        with (
            patch.dict(os.environ, {**settings, "META_MODEL_VERIFIED": "false"}, clear=True),
            self.assertRaisesRegex(RuntimeError, "verified provider"),
        ):
            configure_deployment()
        with patch.dict(os.environ, {"DATABASE_URL": settings["DATABASE_URL"]}, clear=True):
            configure_deployment()
            self.assertEqual(os.environ["MODEL_INFERENCE_ENABLED"], "false")

    def test_profile_rejects_ephemeral_database_before_modifying_environment(self):
        for database in ("", "sqlite:///:memory:", "local-app.db"):
            with (
                self.subTest(database=database),
                patch.dict(
                    os.environ,
                    {"DATABASE_URL": database, "MODEL_INFERENCE_ENABLED": "true"},
                    clear=True,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "persistent PostgreSQL"):
                    configure_replay()
                self.assertEqual(os.environ["MODEL_INFERENCE_ENABLED"], "true")

    def test_replay_enforced_and_worker_cannot_inherit_signing_or_provider_secrets(self):
        secret_names = (
            "AUTH_ED25519_PRIVATE_KEY",
            "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS",
            "AUTH_TOKEN_PEPPER",
            "AUTH_INVITE_CODE",
            "API_BEARER_TOKEN",
            "META_MODEL_API_KEY",
            "MODEL_API_KEY",
        )
        environment = dict.fromkeys(secret_names, "synthetic-test-secret")
        environment.update(
            DATABASE_URL="postgresql://example.invalid/research", MODEL_INFERENCE_ENABLED="true"
        )
        with patch.dict(os.environ, environment, clear=True):
            configure_replay()
            self.assertEqual(os.environ["APP_ENV"], "production")
            self.assertEqual(os.environ["MODEL_INFERENCE_ENABLED"], "false")
            self.assertEqual(os.environ["RESEARCH_INLINE_WORKER"], "false")
            self.assertIn("AUTH_ED25519_PRIVATE_KEY", os.environ)
            self.assertNotIn("META_MODEL_API_KEY", os.environ)
            configure_replay(worker=True)
            self.assertTrue(all(name not in os.environ for name in secret_names))
            self.assertIn("DATABASE_URL", os.environ)

    def test_render_hostname_is_exact_and_explicit_allowlist_wins(self):
        base = {"DATABASE_URL": "postgresql://example.invalid/research"}
        for host in (
            "neurolab-api.onrender.com",
            "*",
            "bad.example/path",
            "https://example.com",
            "",
        ):
            with (
                self.subTest(host=host),
                patch.dict(os.environ, {**base, "RENDER_EXTERNAL_HOSTNAME": host}, clear=True),
            ):
                configure_replay()
                self.assertEqual(
                    os.environ.get("ALLOWED_HOSTS"),
                    host if host == "neurolab-api.onrender.com" else None,
                )
        with patch.dict(
            os.environ,
            {
                **base,
                "RENDER_EXTERNAL_HOSTNAME": "new.onrender.com",
                "ALLOWED_HOSTS": "chosen.example",
            },
            clear=True,
        ):
            configure_replay()
            self.assertEqual(os.environ["ALLOWED_HOSTS"], "chosen.example")

    def test_shutdown_finishes_current_claim_and_never_claims_another(self):
        stop = threading.Event()
        finished = []

        def execute():
            stop.set()
            finished.append("completed current task")
            return True

        worker = Mock()
        worker.run_once.side_effect = execute
        poll_queue(worker, stop)
        worker.run_once.assert_called_once()
        self.assertEqual(finished, ["completed current task"])
        poll_queue(worker, stop)
        worker.run_once.assert_called_once()

    def test_real_sigterm_drains_current_work_and_closes_store(self):
        program = """
import os, signal
from unittest.mock import Mock, patch
from neurolab.worker import main
store, worker = Mock(), Mock()
def task():
    os.kill(os.getpid(), signal.SIGTERM)
    return True
worker.run_once.side_effect = task
with patch('neurolab.store.RunStore', return_value=store), patch('neurolab.ghana.load_ghana'), patch('neurolab.worker.QueueWorker', return_value=worker), patch('sys.argv', ['worker']):
    main()
worker.run_once.assert_called_once()
store.close.assert_called_once()
"""
        result = subprocess.run(  # noqa: S603 - fixed interpreter and synthetic local signal harness
            [sys.executable, "-c", program], capture_output=True, text=True, timeout=10, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_once_and_idle_shutdown_do_not_busy_poll(self):
        worker = Mock()
        worker.run_once.return_value = False
        stop = Mock()
        stop.is_set.side_effect = [False, True]
        poll_queue(worker, stop, poll_seconds=2)
        stop.wait.assert_called_once_with(2)
        worker.reset_mock()
        poll_queue(worker, threading.Event(), once=True)
        worker.run_once.assert_called_once()

    def test_deployment_revision_without_git_is_strict_and_local_git_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for value in ("a" * 40, "b" * 64, "not-a-commit", "../../private"):
                with (
                    self.subTest(value=value),
                    patch.dict(os.environ, {"VERCEL_GIT_COMMIT_SHA": value}),
                ):
                    self.assertEqual(git_revision(root), value if len(value) in (40, 64) else None)
            with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "d" * 40}, clear=True):
                self.assertEqual(git_revision(root), "d" * 40)
            (root / ".git").mkdir()
            (root / ".git/HEAD").write_text("c" * 40)
            with patch.dict(os.environ, {"VERCEL_GIT_COMMIT_SHA": "a" * 40}):
                self.assertEqual(git_revision(root), "c" * 40)
