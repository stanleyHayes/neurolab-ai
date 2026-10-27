"""Isolated real-CSV queue, transaction, cross-connection and worker tests."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qsl, quote, urlencode, urlsplit

from neurolab.agent import ResearchAgent
from neurolab.execution import execute_run
from neurolab.ghana import load_ghana
from neurolab.jobs import LeaseCheckedAdapter, QueueLimitError, ResearchJobs
from neurolab.research_context import (
    ResearchConfiguration,
    ResearchRunRequest,
    build_deterministic_plan,
)
from neurolab.store import ExecutionCancelled, ExecutionLeaseLost, RunStore
from neurolab.worker import QueueWorker

ROOT = Path(__file__).resolve().parents[1]


class DurableJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_ghana()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temporary.name) / "jobs.db")
        self.pg_base = os.getenv("NEUROLAB_TEST_POSTGRES_URL")
        if self.pg_base:
            import psycopg
            from psycopg import sql
            from psycopg.conninfo import conninfo_to_dict

            if not conninfo_to_dict(self.pg_base)["dbname"].startswith("neurolab_job_test_"):
                raise ValueError(
                    "PostgreSQL job tests require an explicitly disposable test database"
                )
            self.schema = "job_test_" + uuid.uuid4().hex
            with psycopg.connect(self.pg_base, autocommit=True) as connection:
                connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
            url = urlsplit(self.pg_base)
            query = dict(parse_qsl(url.query))
            query["options"] = "-c search_path=" + self.schema
            self.path = f"{url.scheme}://{url.netloc}{url.path}?{urlencode(query, quote_via=quote)}"
        self.store = RunStore(self.path)
        self.jobs = ResearchJobs(self.store)
        self.owner = self.store.create_user(
            "queue-owner@example.test", "not-a-real-password-hash", "Queue owner"
        )["user_id"]
        self.other = self.store.create_user(
            "queue-other@example.test", "not-a-real-password-hash", "Queue other"
        )["user_id"]
        config = ResearchConfiguration(preferred_methods=["dataset_profile"])
        self.request = ResearchRunRequest(
            objective="Profile the actual source.",
            configuration=config,
            plan=build_deterministic_plan("Profile the actual source.", config),
        )

    def tearDown(self):
        self.store.close()
        if self.pg_base:
            import psycopg
            from psycopg import sql

            with psycopg.connect(self.pg_base, autocommit=True) as connection:
                connection.execute(
                    sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema))
                )
        self.temporary.cleanup()

    def enqueue(self, owner=None, **kwargs):
        return self.jobs.enqueue(
            self.request, owner or self.owner, self.dataset.source_sha256, **kwargs
        )

    def expire(self, run_id, *, deadline=False):
        with self.store.atomic():
            now = self.store.database_epoch()
            self.store._execute(
                "UPDATE research_jobs SET lease_until = ? WHERE run_id = ?", (now - 1, run_id)
            )
            if deadline:
                self.store._execute(
                    "UPDATE research_jobs SET deadline = ? WHERE run_id = ?", (now - 1, run_id)
                )

    def test_queued_request_survives_connection_restart_and_executes_once(self):
        rid = self.enqueue()
        self.store.close()
        self.store = RunStore(self.path)
        self.jobs = ResearchJobs(self.store)
        worker = QueueWorker(
            self.store, lambda req, key: execute_run(self.store, self.dataset, req, key)
        )
        self.assertTrue(worker.run_once())
        self.assertFalse(worker.run_once())
        run = self.store.get_run(rid)
        self.assertEqual(run["status"], "COMPLETE")
        self.assertEqual(run["report"]["objective"], self.request.objective)
        self.assertEqual(run["report"]["tool_calls"], 1)
        self.assertEqual(len(self.store.list_artifacts(rid)), 1)
        self.assertEqual(self.jobs.public_status(rid, self.owner)["attempts"], 1)
        self.assertEqual(self.jobs.public_status(rid, self.owner)["state"], "DONE")
        self.assertEqual(self.store.list_artifacts(rid)[0]["results"]["row_count"], 864)

    def test_global_and_owner_admission_are_atomic_across_connections(self):
        barrier = threading.Barrier(4)

        def submit(_):
            store = RunStore(self.path)
            try:
                barrier.wait()
                try:
                    return ResearchJobs(store).enqueue(
                        self.request, self.owner, self.dataset.source_sha256
                    )
                except QueueLimitError:
                    return None
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=4) as pool:
            runs = list(pool.map(submit, range(4)))
        self.assertEqual(len([r for r in runs if r]), 2)
        self.assertEqual(self.store.count_active_runs(self.owner), 2)
        self.assertEqual(len(self.store.list_runs(owner_user_id=self.owner)), 2)
        with self.assertRaises(QueueLimitError):
            self.enqueue(self.other, queue_limit=2)
        self.assertEqual(self.store.list_runs(owner_user_id=self.other), [])

    def test_exclusive_claim_and_global_execution_limit(self):
        rid = self.enqueue()
        second = self.enqueue(self.other)
        barrier = threading.Barrier(2)

        def claim(_):
            store = RunStore(self.path)
            try:
                barrier.wait()
                return ResearchJobs(store).claim("explicit-test-worker", run_id=rid, max_running=1)
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(claim, range(2)))
        self.assertEqual(sum(c is not None for c in claims), 1)
        self.assertIsNone(self.jobs.claim("other-worker", run_id=second, max_running=1))

    def test_lease_expiry_fences_late_writes_and_provider_calls_without_retry(self):
        rid = self.enqueue()
        claim = self.jobs.claim("test-worker")
        self.expire(rid)
        adapter = Mock(provider="test-only", model_id="not-a-model-call")
        guarded = LeaseCheckedAdapter(adapter, self.store)
        with self.assertRaises(ExecutionLeaseLost), self.store.execution_lease(rid, claim["token"]):
            guarded.generate_structured([], {}, timeout=1)
        adapter.generate_structured.assert_not_called()
        self.jobs.reconcile()
        self.assertEqual(self.store.get_run(rid)["status"], "FAILED")
        self.assertEqual(self.jobs.public_status(rid, self.owner)["state"], "INTERRUPTED")
        self.assertIsNone(self.jobs.claim("new-worker", run_id=rid))
        self.assertEqual(self.store.list_artifacts(rid), [])
        self.assertFalse(self.jobs.renew(rid, claim["token"]))
        self.assertFalse(self.jobs.finish(rid, claim["token"]))

    def test_expiry_after_execution_context_entry_rolls_back_late_result(self):
        rid = self.enqueue()
        claim = self.jobs.claim("test-worker")
        adapter = Mock(provider="test-only", model_id="not-a-real-model")
        guarded = LeaseCheckedAdapter(adapter, self.store, rid)
        with (
            self.store.execution_lease(rid, claim["token"]),
            patch.object(self.store, "database_epoch", return_value=10**15),
        ):
            with self.assertRaises(ExecutionLeaseLost):
                self.store.add_event(rid, "test.late-result", {"value": "not published"})
            with self.assertRaises(ExecutionLeaseLost):
                guarded.generate_structured([], {}, timeout=1)
            with self.assertRaises(ExecutionLeaseLost):
                guarded.generate_refinement([], {}, timeout=1)
        adapter.generate_structured.assert_not_called()
        adapter.generate_refinement.assert_not_called()
        self.assertFalse(
            any(e["event_type"] == "test.late-result" for e in self.store.list_events(rid))
        )
        self.expire(rid, deadline=True)
        self.jobs.reconcile()
        self.assertEqual(self.store.get_run(rid)["status"], "TIMED_OUT")
        self.assertEqual(self.jobs.public_status(rid, self.owner)["state"], "TIMED_OUT")

    def test_heartbeat_renews_only_live_owner_and_closes_completed_job(self):
        rid = self.enqueue()
        claim = self.jobs.claim("test-worker", lease_seconds=1)
        self.assertFalse(self.jobs.renew(rid, "wrong-token"))
        self.assertTrue(self.jobs.renew(rid, claim["token"], lease_seconds=30))
        with self.store.execution_lease(rid, claim["token"]):
            execute_run(self.store, self.dataset, self.request, rid)
        self.expire(rid)
        self.jobs.reconcile()
        self.assertEqual(self.store.get_run(rid)["status"], "COMPLETE")
        self.assertEqual(self.jobs.public_status(rid, self.owner)["state"], "DONE")

    def test_queued_cancel_and_owner_isolation(self):
        rid = self.enqueue()
        self.assertIsNone(self.jobs.cancel(rid, self.other))
        self.assertIsNone(self.jobs.public_status(rid, self.other))
        self.assertIsNotNone(self.jobs.cancel(rid, self.owner))
        self.assertEqual(self.store.get_run(rid)["status"], "CANCELLED")
        self.assertIsNone(self.jobs.claim("never-started"))
        self.assertIsNone(self.jobs.cancel(rid, self.owner))
        self.assertNotIn("claim_token", self.jobs.public_status(rid, self.owner))

    def test_disabled_owner_and_unowned_legacy_are_never_claimed(self):
        legacy = self.store.create_run("ghana_combined", "Legacy record", "hash", 2026)
        self.store.update_status(legacy, "RUNNING")
        rid = self.enqueue()
        with self.store.atomic():
            self.store._execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (self.owner,))
        self.assertIsNone(self.jobs.claim("worker"))
        self.assertEqual(self.store.get_run(rid)["status"], "CANCELLED")
        self.assertEqual(self.store.get_run(legacy)["status"], "RUNNING")
        self.assertIsNone(self.jobs.public_status(legacy, self.owner))
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_admission_and_terminal_report_roll_back_as_units(self):
        with (
            patch.object(
                self.store, "set_stage", side_effect=RuntimeError("explicit test failure")
            ),
            self.assertRaises(RuntimeError),
        ):
            self.enqueue()
        self.assertEqual(self.store.list_runs(owner_user_id=self.owner), [])
        rid = self.enqueue()
        claim = self.jobs.claim("test-worker")
        original = self.store.add_event

        def fail_report(key, event, payload):
            if event == "report.generated":
                raise RuntimeError("explicit finalization test")
            return original(key, event, payload)

        agent = ResearchAgent(
            self.dataset,
            self.store,
            configuration=self.request.configuration,
            research_plan=self.request.plan,
        )
        with (
            self.store.execution_lease(rid, claim["token"]),
            patch.object(self.store, "add_event", side_effect=fail_report),
            self.assertRaises(RuntimeError),
        ):
            agent.run(self.request.objective, run_id=rid)
        self.assertIsNone(self.store.get_run(rid)["report"])
        self.assertFalse(
            any(e["event_type"] == "run.completed" for e in self.store.list_events(rid))
        )

    def test_nested_caught_failure_cannot_commit_partial_transaction(self):
        caught = []

        def catch_nested_failure():
            with self.store.atomic():
                try:
                    with self.store.atomic():
                        self.store.request_cancel("nonexistent")
                        raise ValueError("explicit nested failure")
                except ValueError:
                    caught.append(True)

        with self.assertRaises(RuntimeError):
            catch_nested_failure()
        self.assertEqual(caught, [True])

    def test_worker_captures_failure_and_keeps_available_evidence(self):
        rid = self.enqueue()

        def fail(req, key):
            raise RuntimeError("private exception text")

        worker = QueueWorker(self.store, fail)
        self.assertTrue(worker.run_once())
        self.assertEqual(self.store.get_run(rid)["status"], "FAILED")
        self.assertNotIn("private exception text", json.dumps(self.store.list_events(rid)))
        self.assertFalse(worker.run_once())
        with self.assertRaises(ValueError):
            QueueWorker(self.store, fail, lease_seconds=0)
        with self.assertRaises(ValueError):
            self.jobs.claim("test", max_running=0)
        with self.assertRaises(ValueError):
            self.enqueue(owner_limit=0)

    def test_source_change_prevents_any_provider_or_tool_execution(self):
        rid = self.jobs.enqueue(
            self.request.model_copy(update={"mode": "meta"}), self.owner, "0" * 64
        )
        provider = Mock()
        QueueWorker(
            self.store,
            lambda req, key: execute_run(
                self.store, self.dataset, req, key, adapter_factory=provider
            ),
        ).run_once()
        provider.assert_not_called()
        self.assertEqual(self.store.get_run(rid)["status"], "FAILED")
        self.assertEqual(self.store.list_artifacts(rid), [])

    def test_claimed_cancellation_prevents_provider_and_numeric_work(self):
        rid = self.jobs.enqueue(
            self.request.model_copy(update={"mode": "meta"}), self.owner, self.dataset.source_sha256
        )
        claim = self.jobs.claim("test-worker")
        self.store.request_cancel(rid)
        adapter = Mock(provider="test-only", model_id="fixture-only")
        guarded = LeaseCheckedAdapter(adapter, self.store, rid)
        with self.store.execution_lease(rid, claim["token"]):
            with self.assertRaises(ExecutionCancelled):
                guarded.generate_refinement([], {}, timeout=1)
            execute_run(
                self.store,
                self.dataset,
                self.request.model_copy(update={"mode": "meta"}),
                rid,
                adapter_factory=adapter,
            )
        adapter.assert_not_called()
        adapter.generate_refinement.assert_not_called()
        self.assertEqual(self.store.get_run(rid)["status"], "CANCELLED")
        self.assertEqual(self.store.list_artifacts(rid), [])
        self.jobs.finish(rid, claim["token"])
        # Fixture-only model response cancels while a decision is in flight;
        # the already-returned decision must not start a new numeric tool.
        next_request = self.request.model_copy(update={"mode": "meta"})
        next_id = self.jobs.enqueue(next_request, self.owner, self.dataset.source_sha256)
        fixture = Mock(provider="test-only", model_id="fixture-only")

        def cancel_during_decision(*args, **kwargs):
            self.store.request_cancel(next_id)
            return {
                "action": "dataset_profile",
                "bootstrap_samples": None,
                "decision_summary": "Explicit test-only cancellation response",
            }

        fixture.generate_structured.side_effect = cancel_during_decision
        worker = QueueWorker(
            self.store,
            lambda request, key: execute_run(
                self.store, self.dataset, request, key, adapter_factory=lambda: fixture
            ),
        )
        worker.run_once(run_id=next_id)
        self.assertEqual(fixture.generate_structured.call_count, 1)
        self.assertEqual(self.store.get_run(next_id)["status"], "CANCELLED")
        self.assertEqual(self.store.list_artifacts(next_id), [])
        self.assertFalse(
            any(e["event_type"] == "tool.requested" for e in self.store.list_events(next_id))
        )

    def test_heartbeat_reconciles_expiry_and_retries_transient_database_outage(self):
        worker = QueueWorker(self.store, Mock())
        worker.jobs = Mock()
        worker.jobs.renew.return_value = False
        worker._heartbeat(Mock(wait=Mock(return_value=False)), {"run_id": "test", "token": "test"})
        worker.jobs.reconcile.assert_called_once()
        worker.jobs.reset_mock()
        worker.jobs.renew.side_effect = [RuntimeError("private DB exception"), True]
        with self.assertLogs("neurolab.worker", level="WARNING") as logs:
            worker._heartbeat(
                Mock(wait=Mock(side_effect=[False, False, True])),
                {"run_id": "test", "token": "test"},
            )
        self.assertEqual(worker.jobs.renew.call_count, 2)
        self.assertNotIn("private DB exception", str(logs.output))

    def test_all_nonterminal_stages_consume_owner_quota(self):
        for _ in range(2):
            rid = self.enqueue()
            self.store.set_stage(rid, "VALIDATING", "Explicit test stage")
        with self.assertRaises(QueueLimitError):
            self.enqueue()

    def test_artifact_and_completion_event_publish_atomically(self):
        rid = self.enqueue()
        original = self.store.add_event

        def fail(key, event, payload):
            if event == "tool.completed":
                raise RuntimeError("Explicit publication test failure")
            return original(key, event, payload)

        with patch.object(self.store, "add_event", side_effect=fail):
            report = ResearchAgent(
                self.dataset,
                self.store,
                configuration=self.request.configuration,
                research_plan=self.request.plan,
                max_steps=1,
                max_tool_calls=1,
            ).run(self.request.objective, run_id=rid)["report"]
        self.assertEqual(self.store.list_artifacts(rid), [])
        self.assertEqual(report["completion_status"], "partial")
        self.assertEqual(report["evidence_ids"], [])

    def test_owned_historical_queued_cancel_does_not_adopt_job(self):
        rid = self.store.create_run(
            "ghana_combined",
            "Historical owned request",
            self.dataset.source_sha256,
            2026,
            self.owner,
        )
        self.store.set_stage(rid, "QUEUED", "Explicit test historical queue state")
        self.assertIsNotNone(self.jobs.cancel(rid, self.owner))
        self.assertEqual(self.store.get_run(rid)["status"], "CANCELLED")
        self.assertIsNone(self.jobs.public_status(rid, self.owner))

    def test_owner_deactivation_fences_a_claimed_worker(self):
        rid = self.enqueue()
        claim = self.jobs.claim("test-worker")
        with self.store.atomic():
            self.store._execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (self.owner,))
        self.assertFalse(self.jobs.renew(rid, claim["token"]))
        with self.assertRaises(ExecutionLeaseLost), self.store.execution_lease(rid, claim["token"]):
            self.store.add_event(rid, "test.unpublished", {})
        self.jobs.reconcile()
        self.assertEqual(self.store.get_run(rid)["status"], "CANCELLED")
        self.assertEqual(self.store.list_artifacts(rid), [])
        cancelled = next(
            e for e in self.store.list_events(rid) if e["event_type"] == "run.cancelled"
        )
        self.assertEqual(cancelled["payload"]["reason"], "owner_inactive")

    def test_standalone_worker_process_needs_no_jwt_key_or_provider(self):
        rid = self.enqueue()
        environment = {**os.environ, "DATABASE_URL": self.path, "MODEL_INFERENCE_ENABLED": "false"}
        environment.pop("AUTH_ED25519_PRIVATE_KEY", None)
        completed = subprocess.run(
            [sys.executable, "-m", "neurolab.worker", "--once"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.store.get_run(rid)["status"], "COMPLETE")
        self.assertEqual(self.jobs.public_status(rid, self.owner)["state"], "DONE")
