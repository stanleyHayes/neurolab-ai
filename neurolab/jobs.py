"""SQL-backed admission, exclusive worker leases and explicit interrupted jobs.

Queued work survives API restart. Started work is never automatically retried:
provider billing may be unknown after a crash. Only new, owned jobs participate;
legacy runs are neither adopted nor made public.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from .providers import StructuredModelAdapter
from .research_context import objective_digest
from .store import ExecutionCancelled

TERMINAL = {"COMPLETE", "PARTIAL", "FAILED", "CANCELLED", "TIMED_OUT"}


class QueueLimitError(ValueError):
    pass


class ResearchJobs:
    def __init__(self, store):
        self.store = store

    def _control(self):
        self.store._execute("UPDATE queue_control SET revision = revision + 1 WHERE control_id = 1")

    def enqueue(
        self,
        request,
        owner_user_id,
        source_sha256,
        *,
        owner_limit=2,
        queue_limit=100,
        initial_plan=None,
    ):
        if owner_limit < 1 or queue_limit < 1:
            raise ValueError("Job limits must be positive")
        config = request.configuration
        plan = request.plan or initial_plan
        if config is None or plan is None:
            raise ValueError("A validated configuration and plan are required")
        with self.store.atomic():
            self._control()
            user = self.store.get_user(owner_user_id)
            if not user or not user["is_active"]:
                raise ValueError("An active owner is required")
            if self.store.count_active_runs(owner_user_id) >= owner_limit:
                raise QueueLimitError("You already have the maximum number of active runs")
            queued = self.store._execute(
                "SELECT COUNT(*) AS n FROM research_jobs WHERE state = 'QUEUED'"
            ).fetchone()["n"]
            if queued >= queue_limit:
                raise QueueLimitError("The research queue is full; try again later")
            run_id = self.store.create_run(
                config.dataset_id,
                request.objective,
                source_sha256,
                request.seed,
                owner_user_id=owner_user_id,
                research_configuration=config.model_dump(mode="json"),
                research_plan=plan.model_dump(mode="json"),
            )
            self.store._execute(
                "INSERT INTO research_jobs (run_id, request_json, state, created_at) VALUES (?, ?, ?, ?)",
                (run_id, request.model_dump_json(), "QUEUED", self.store._now()),
            )
            self.store.add_event(
                run_id,
                "request.accepted",
                {
                    "mode": request.mode,
                    "max_steps": config.constraints.max_steps,
                    "max_tool_calls": config.constraints.max_tool_calls,
                    "objective_characters": len(request.objective),
                    "objective_sha256": objective_digest(request.objective),
                },
            )
            self.store.add_event(
                run_id,
                "job.queued",
                {
                    "public_summary": "Validated request persisted for bounded worker execution; no tools have run."
                },
            )
            self.store.set_stage(run_id, "QUEUED", "Run durably queued for bounded execution")
            return run_id

    def _finish_job(self, run_id, state):
        self.store._execute(
            "UPDATE research_jobs SET state = ?, claim_token = NULL, lease_until = NULL, finished_at = ? WHERE run_id = ?",
            (state, self.store._now(), run_id),
        )

    def _reconcile_row(self, row, now):
        run_id = row["run_id"]
        if row["status"] in TERMINAL:
            self._finish_job(run_id, "DONE")
        elif not row["is_active"] or (row["state"] == "QUEUED" and row["cancel_requested"]):
            self.store.add_event(
                run_id, "run.cancelled", {"reason": "cancelled_or_owner_inactive_before_execution"}
            )
            self._finish_job(run_id, "CANCELLED")
        elif row["state"] == "RUNNING" and row["lease_until"] <= now:
            self._expire(run_id, row["deadline"] <= now)

    def _expire(self, run_id, timed_out):
        self.store.set_stage(
            run_id,
            "TIMED_OUT" if timed_out else "FAILED",
            "Execution deadline exceeded"
            if timed_out
            else "Worker lease expired; started work is not automatically retried",
        )
        self.store.add_event(
            run_id,
            "run.timed_out" if timed_out else "run.failed",
            {
                "error_type": "ExecutionDeadlineExceeded" if timed_out else "WorkerLeaseExpired",
                "message": "Execution deadline exceeded."
                if timed_out
                else "Worker lease expired; completed artifacts are retained. Started work is not automatically retried.",
                "retryable": False,
            },
        )
        self._finish_job(run_id, "TIMED_OUT" if timed_out else "INTERRUPTED")

    def _reconcile(self):
        now = self.store.database_epoch()
        query = (
            "SELECT j.run_id, j.state, j.lease_until, j.deadline, r.status, r.cancel_requested, u.is_active "
            "FROM research_jobs j JOIN runs r ON r.run_id = j.run_id JOIN users u ON u.user_id = r.owner_user_id "
            "WHERE j.state IN ('QUEUED', 'RUNNING') ORDER BY j.run_id"
        )
        if self.store._connection.is_postgresql:
            query += " FOR UPDATE OF j"
        rows = self.store._execute(query).fetchall()
        for row in rows:
            self._reconcile_row(row, now)

    def reconcile(self):
        with self.store.atomic():
            self._control()
            self._reconcile()

    def claim(self, worker_id, *, run_id=None, lease_seconds=30, max_running=2):
        if not 1 <= lease_seconds <= 120 or max_running < 1:
            raise ValueError("Invalid worker lease or concurrency limit")
        with self.store.atomic():
            self._control()
            self._reconcile()
            running = self.store._execute(
                "SELECT COUNT(*) AS n FROM research_jobs WHERE state = 'RUNNING'"
            ).fetchone()["n"]
            if running >= max_running:
                return None
            query = "SELECT j.run_id, j.request_json FROM research_jobs j JOIN runs r ON r.run_id = j.run_id WHERE j.state = 'QUEUED'"
            parameters = ()
            if run_id is not None:
                query += " AND j.run_id = ?"
                parameters = (run_id,)
            row = self.store._execute(
                query + " ORDER BY j.created_at, j.run_id LIMIT 1", parameters
            ).fetchone()
            if row is None:
                return None
            request = json.loads(row["request_json"])
            now = self.store.database_epoch()
            deadline = now + request["configuration"]["constraints"]["max_seconds"]
            token = str(uuid.uuid4())
            self.store._execute(
                "UPDATE research_jobs SET state = 'RUNNING', claim_token = ?, worker_id = ?, lease_until = ?, deadline = ?, attempts = attempts + 1, started_at = ? WHERE run_id = ?",
                (
                    token,
                    worker_id,
                    min(now + lease_seconds, deadline),
                    deadline,
                    self.store._now(),
                    row["run_id"],
                ),
            )
            self.store.add_event(
                row["run_id"],
                "job.claimed",
                {"public_summary": "Worker acquired an exclusive execution lease.", "attempt": 1},
            )
            self.store.set_stage(
                row["run_id"],
                "PLANNING",
                "Worker acquired the lease and is preparing bounded execution",
            )
            return {"run_id": row["run_id"], "token": token, "request": request}

    def renew(self, run_id, token, *, lease_seconds=30):
        with self.store.atomic():
            now = self.store.database_epoch()
            query = (
                "SELECT j.state, j.claim_token, j.lease_until, j.deadline, u.is_active FROM research_jobs j "
                "JOIN runs r ON r.run_id = j.run_id JOIN users u ON u.user_id = r.owner_user_id WHERE j.run_id = ?"
            )
            if self.store._connection.is_postgresql:
                query += " FOR UPDATE OF j"
            row = self.store._execute(query, (run_id,)).fetchone()
            if (
                not row
                or row["state"] != "RUNNING"
                or row["claim_token"] != token
                or row["lease_until"] <= now
                or row["deadline"] <= now
                or not row["is_active"]
            ):
                return False
            self.store._execute(
                "UPDATE research_jobs SET lease_until = ? WHERE run_id = ?",
                (min(now + lease_seconds, row["deadline"]), run_id),
            )
            return True

    def finish(self, run_id, token):
        with self.store.atomic():
            self._control()
            self._reconcile()
            row = self.store._execute(
                "SELECT claim_token, state FROM research_jobs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row or row["claim_token"] != token or row["state"] != "RUNNING":
                return False
            run = self.store.get_run(run_id)
            if run["status"] not in TERMINAL:
                self.store.add_event(
                    run_id,
                    "run.failed",
                    {
                        "error_type": "WorkerReturnedWithoutTerminalState",
                        "message": "Worker returned without a terminal research state; no completion is inferred.",
                        "retryable": False,
                    },
                )
            self._finish_job(run_id, "DONE")
            return True

    def cancel(self, run_id, owner_user_id):
        with self.store.atomic():
            self._control()
            query = "SELECT run_id, status FROM runs WHERE run_id = ? AND owner_user_id = ?"
            if self.store._connection.is_postgresql:
                query += " FOR UPDATE"
            run = self.store._execute(query, (run_id, owner_user_id)).fetchone()
            if not run or run["status"] in TERMINAL:
                return None
            self.store.request_cancel(run_id)
            event = self.store.add_event(
                run_id,
                "run.cancel_requested",
                {"note": "Cancellation will be applied at the next safe boundary"},
            )
            row = self.store._execute(
                "SELECT state FROM research_jobs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if (row and row["state"] == "QUEUED") or (
                row is None and run["status"] in {"CREATED", "QUEUED"}
            ):
                self.store.add_event(
                    run_id, "run.cancelled", {"reason": "cancelled_before_execution"}
                )
                if row:
                    self._finish_job(run_id, "CANCELLED")
            return event

    def public_status(self, run_id, owner_user_id):
        if self.store.get_run(run_id, owner_user_id=owner_user_id) is None:
            return None
        with self.store._lock:
            row = self.store._execute(
                "SELECT state, attempts, created_at, started_at, finished_at FROM research_jobs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            return dict(row) if row else None


class LeaseCheckedAdapter(StructuredModelAdapter):
    def __init__(self, adapter: StructuredModelAdapter, store, run_id=None):
        self.adapter, self.store, self.run_id = adapter, store, run_id
        self.provider, self.model_id = adapter.provider, adapter.model_id

    def _guard(self):
        self.store.assert_execution_lease()
        if self.run_id is not None and self.store.cancel_requested(self.run_id):
            raise ExecutionCancelled("Owner cancelled before another provider call")

    def generate_structured(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]:
        self._guard()
        return self.adapter.generate_structured(messages, schema, timeout=timeout)

    def generate_refinement(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]:
        self._guard()
        return self.adapter.generate_refinement(messages, schema, timeout=timeout)
