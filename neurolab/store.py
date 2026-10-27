"""Database-backed event/artifact store for reproducible research runs."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

POSTGRESQL_SCHEME = "postgresql://"
POSTGRES_SCHEME = "postgres://"
UTC_OFFSET = "+00:00"
REVOKE_SESSION_FAMILY_SQL = (
    "UPDATE auth_sessions SET revoked_at = ? WHERE family_id = ? AND revoked_at IS NULL"
)


class _DatabaseConnection:
    """Small DB-API adapter for SQLite tests and PostgreSQL deployments."""

    def __init__(self, database_url: str) -> None:
        self.is_postgresql = database_url.startswith(
            (POSTGRESQL_SCHEME, POSTGRES_SCHEME, "postgresql+psycopg://")
        )
        self._transactions = []
        if self.is_postgresql:
            import psycopg
            from psycopg.rows import dict_row

            conninfo = database_url.replace("postgresql+psycopg://", POSTGRESQL_SCHEME, 1)
            if conninfo.startswith(POSTGRES_SCHEME):
                conninfo = POSTGRESQL_SCHEME + conninfo.removeprefix(POSTGRES_SCHEME)
            self.connection = psycopg.connect(conninfo, row_factory=dict_row, autocommit=True)
        else:
            sqlite_path = database_url.removeprefix("sqlite:///")
            self.connection = sqlite3.connect(sqlite_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row

    def __enter__(self):
        if self.is_postgresql:
            transaction = self.connection.transaction()
            self._transactions.append(transaction)
            return transaction.__enter__()
        return self.connection.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_postgresql:
            transaction = self._transactions.pop()
            return transaction.__exit__(exc_type, exc_value, traceback)
        return self.connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, query: str, parameters: tuple[Any, ...] = ()):
        if self.is_postgresql:
            query = query.replace("?", "%s")
        return self.connection.execute(query, parameters)

    def executescript(self, script: str) -> None:
        if self.is_postgresql:
            for statement in script.split(";"):
                if statement.strip():
                    self.execute(statement)
        else:
            self.connection.executescript(script)

    def close(self) -> None:
        self.connection.close()


class RunStore:
    def __init__(self, path: Path | str = ":memory:") -> None:
        self.path = str(path)
        self._connection = _DatabaseConnection(self.path)
        self._lock = threading.RLock()
        with self._lock, self._connection:
            if not self._connection.is_postgresql:
                self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'researcher',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    password_changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    refresh_token_hash TEXT NOT NULL UNIQUE,
                    csrf_token_hash TEXT NOT NULL,
                    family_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    rotated_at TEXT,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS auth_sessions_user_idx ON auth_sessions(user_id);
                CREATE INDEX IF NOT EXISTS auth_sessions_family_idx ON auth_sessions(family_id);
                CREATE TABLE IF NOT EXISTS auth_rate_limits (
                    identifier_hash TEXT PRIMARY KEY,
                    failures INTEGER NOT NULL,
                    blocked_until TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS auth_login_limits (
                    identifier_hash TEXT PRIMARY KEY,
                    failures INTEGER NOT NULL,
                    blocked_until TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    owner_user_id TEXT REFERENCES users(user_id) ON DELETE RESTRICT,
                    dataset_id TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
 report_json TEXT,
 cancel_requested INTEGER NOT NULL DEFAULT 0,
 research_configuration_json TEXT,
 research_plan_json TEXT
 );
                CREATE TABLE IF NOT EXISTS events (
                    run_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (run_id, sequence),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                );
CREATE TABLE IF NOT EXISTS research_drafts (
 owner_user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
 revision INTEGER NOT NULL,
 draft_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
                """
            )
            if self._connection.is_postgresql:
                rows = self._connection.execute(
                    "SELECT column_name AS name FROM information_schema.columns "
                    "WHERE table_schema = current_schema() AND table_name = 'runs'"
                ).fetchall()
            else:
                rows = self._connection.execute("PRAGMA table_info(runs)").fetchall()
            run_columns = {row["name"] for row in rows}
            if "owner_user_id" not in run_columns:
                self._connection.execute(
                    "ALTER TABLE runs ADD COLUMN owner_user_id TEXT "
                    "REFERENCES users(user_id) ON DELETE RESTRICT"
                )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS runs_owner_created_idx "
                "ON runs(owner_user_id, created_at DESC)"
            )
            if self._connection.is_postgresql:
                rows = self._connection.execute(
                    "SELECT column_name AS name FROM information_schema.columns "
                    "WHERE table_schema = current_schema() AND table_name = 'runs'"
                ).fetchall()
            else:
                rows = self._connection.execute("PRAGMA table_info(runs)").fetchall()
            columns = {row["name"] for row in rows}
            if "cancel_requested" not in columns:
                self._connection.execute(
                    "ALTER TABLE runs ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0"
                )
        if "research_configuration_json" not in columns:
            self._connection.execute("ALTER TABLE runs ADD COLUMN research_configuration_json TEXT")
        if "research_plan_json" not in columns:
            self._connection.execute("ALTER TABLE runs ADD COLUMN research_plan_json TEXT")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat().replace(UTC_OFFSET, "Z")

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        with self._connection:
            yield

    def _execute(self, query: str, parameters: tuple[Any, ...] = ()):
        return self._connection.execute(query, parameters)

    def reopen(self) -> None:
        """Reinitialize the same configured database connection after close (tests only)."""
        if self._connection.is_postgresql:
            raise RuntimeError("RunStore.reopen is only supported for isolated SQLite tests")
        self.__init__(self.path)

    def create_run(
        self,
        dataset_id: str,
        objective: str,
        source_sha256: str,
        seed: int,
        owner_user_id: str | None = None,
        research_configuration: dict[str, Any] | None = None,
        research_plan: dict[str, Any] | None = None,
    ) -> str:
        run_id = str(uuid.uuid4())
        now = self._now()
        with self._lock, self._transaction():
            self._execute(
                "INSERT INTO runs (run_id, owner_user_id, dataset_id, objective, source_sha256, seed, status, created_at, updated_at, report_json, research_configuration_json, research_plan_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)",
                (
                    run_id,
                    owner_user_id,
                    dataset_id,
                    objective,
                    source_sha256,
                    seed,
                    "CREATED",
                    now,
                    now,
                    json.dumps(research_configuration, ensure_ascii=False)
                    if research_configuration is not None
                    else None,
                    json.dumps(research_plan, ensure_ascii=False)
                    if research_plan is not None
                    else None,
                ),
            )
            self.add_event(
                run_id, "run.created", {"dataset_id": dataset_id, "source_sha256": source_sha256}
            )
        return run_id

    def update_research_plan(self, run_id: str, plan: dict[str, Any]) -> None:
        with self._lock, self._transaction():
            self._execute(
                "UPDATE runs SET research_plan_json = ?, updated_at = ? WHERE run_id = ?",
                (json.dumps(plan, ensure_ascii=False), self._now(), run_id),
            )

    def save_research_draft(
        self, owner_user_id: str, expected_revision: int, draft: dict[str, Any]
    ) -> dict[str, Any] | None:
        serialized = json.dumps(draft, ensure_ascii=False, separators=(",", ":"))
        now = self._now()
        next_revision = expected_revision + 1
        with self._lock, self._transaction():
            if expected_revision == 0:
                row = self._execute(
                    "INSERT INTO research_drafts (owner_user_id, revision, draft_json, updated_at) "
                    "VALUES (?, ?, ?, ?) ON CONFLICT (owner_user_id) DO NOTHING RETURNING revision",
                    (owner_user_id, next_revision, serialized, now),
                ).fetchone()
            else:
                row = self._execute(
                    "UPDATE research_drafts SET revision = ?, draft_json = ?, updated_at = ? "
                    "WHERE owner_user_id = ? AND revision = ? RETURNING revision",
                    (next_revision, serialized, now, owner_user_id, expected_revision),
                ).fetchone()
            if row is None:
                return None
        return {"revision": int(row["revision"]), "draft": draft, "updated_at": now}

    def get_research_draft(self, owner_user_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._execute(
                "SELECT revision, draft_json, updated_at FROM research_drafts WHERE owner_user_id = ?",
                (owner_user_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "revision": int(row["revision"]),
            "draft": json.loads(row["draft_json"]),
            "updated_at": row["updated_at"],
        }

    def update_research_task(
        self, run_id: str, task_id: str, status: str, evidence_id: str | None = None
    ) -> dict[str, Any] | None:
        """Update a task in persisted run plan JSON and return the new plan."""
        with self._lock, self._transaction():
            row = self._execute(
                "SELECT research_plan_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if row is None or row["research_plan_json"] is None:
                return None
            plan = json.loads(row["research_plan_json"])
            found = False
            for task in plan.get("tasks", []):
                if task.get("task_id") == task_id:
                    task["status"] = status
                    if evidence_id and evidence_id not in task.setdefault("evidence_ids", []):
                        task["evidence_ids"].append(evidence_id)
                    found = True
                    break
            if not found:
                return None
            self._execute(
                "UPDATE runs SET research_plan_json = ?, updated_at = ? WHERE run_id = ?",
                (json.dumps(plan, ensure_ascii=False), self._now(), run_id),
            )
            return plan

    def set_stage(self, run_id: str, stage: str, public_summary: str) -> dict[str, Any]:
        allowed = {
            "CREATED",
            "VALIDATING",
            "PLANNING",
            "PLAN_REVIEW",
            "QUEUED",
            "RUNNING",
            "ANALYZING",
            "COMPLETE",
            "PARTIAL",
            "FAILED",
            "CANCELLED",
            "TIMED_OUT",
        }
        if stage not in allowed:
            raise ValueError(f"Unsupported run stage: {stage}")
        with self._lock:
            event = self.add_event(
                run_id,
                "stage.changed",
                {
                    "stage": stage,
                    "public_summary": public_summary,
                    "progress_completed": None,
                    "progress_total": None,
                    "artifact_refs": [],
                },
            )
            with self._transaction():
                self._execute(
                    "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                    (stage, event["timestamp"], run_id),
                )
        return event

    def update_status(self, run_id: str, status: str) -> None:
        with self._lock, self._transaction():
            self._execute(
                "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (status, self._now(), run_id),
            )

    def request_cancel(self, run_id: str) -> None:
        with self._lock, self._transaction():
            self._execute("UPDATE runs SET cancel_requested = 1 WHERE run_id = ?", (run_id,))

    def cancel_requested(self, run_id: str) -> bool:
        with self._lock:
            row = self._execute(
                "SELECT cancel_requested FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return bool(row["cancel_requested"]) if row else False

    def list_runs(
        self, limit: int = 20, *, owner_user_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._execute(
                "SELECT run_id, dataset_id, objective, source_sha256, seed, status, created_at, updated_at "
                "FROM runs WHERE owner_user_id = ? ORDER BY created_at DESC LIMIT ?",
                (owner_user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_event(self, run_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._transaction():
            row = self._execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 AS next FROM events WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            sequence = int(row["next"])
            event = {
                "event_id": str(uuid.uuid4()),
                "run_id": run_id,
                "sequence": sequence,
                "event_type": event_type,
                "timestamp": self._now(),
                "payload": payload,
            }
            self._execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    sequence,
                    event["event_id"],
                    event_type,
                    event["timestamp"],
                    json.dumps(payload),
                ),
            )
            terminal_status = {
                "run.completed": "COMPLETE",
                "run.partial": "PARTIAL",
                "run.failed": "FAILED",
                "run.cancelled": "CANCELLED",
            }.get(event_type)
            if terminal_status:
                self._execute(
                    "UPDATE runs SET updated_at = ?, status = ? WHERE run_id = ?",
                    (event["timestamp"], terminal_status, run_id),
                )
            else:
                self._execute(
                    "UPDATE runs SET updated_at = ? WHERE run_id = ?",
                    (event["timestamp"], run_id),
                )
        return event

    def add_artifact(self, run_id: str, result: dict[str, Any]) -> None:
        with self._lock, self._transaction():
            self._execute(
                "INSERT INTO artifacts VALUES (?, ?, ?) "
                "ON CONFLICT (artifact_id) DO UPDATE "
                "SET run_id = excluded.run_id, result_json = excluded.result_json",
                (result["artifact_id"], run_id, json.dumps(result, sort_keys=True)),
            )

    def set_report(self, run_id: str, report: dict[str, Any]) -> None:
        with self._lock, self._transaction():
            self._execute(
                "UPDATE runs SET report_json = ?, updated_at = ? WHERE run_id = ?",
                (json.dumps(report, sort_keys=True), self._now(), run_id),
            )

    def get_run(self, run_id: str, *, owner_user_id: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            if owner_user_id is None:
                row = self._execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            else:
                row = self._execute(
                    "SELECT * FROM runs WHERE run_id = ? AND owner_user_id = ?",
                    (run_id, owner_user_id),
                ).fetchone()
            if row is None:
                return None
            data = dict(row)
            report_json = data.pop("report_json", None)
            data["report"] = json.loads(report_json) if report_json else None
            for column, key in (
                ("research_configuration_json", "research_configuration"),
                ("research_plan_json", "research_plan"),
            ):
                raw = data.pop(column, None)
                data[key] = json.loads(raw) if raw else None
            return data

    def list_events(self, run_id: str, *, after_sequence: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._execute(
                "SELECT * FROM events WHERE run_id = ? AND sequence > ? ORDER BY sequence",
                (run_id, after_sequence),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "run_id": row["run_id"],
                "sequence": row["sequence"],
                "event_type": row["event_type"],
                "timestamp": row["timestamp"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._execute(
                "SELECT result_json FROM artifacts WHERE run_id = ? ORDER BY artifact_id",
                (run_id,),
            ).fetchall()
        return [json.loads(row["result_json"]) for row in rows]

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    @staticmethod
    def _public_user(row) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "user_id": row["user_id"],
            "email": row["email"],
            "display_name": row["display_name"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "password_changed_at": row["password_changed_at"],
        }

    def create_user(self, email: str, password_hash: str, display_name: str) -> dict[str, Any]:
        user_id = str(uuid.uuid4())
        now = self._now()
        with self._lock, self._transaction():
            self._execute(
                "INSERT INTO users (user_id, email, password_hash, display_name, role, is_active, "
                "created_at, updated_at, password_changed_at) VALUES (?, ?, ?, ?, 'researcher', 1, ?, ?, ?)",
                (user_id, email, password_hash, display_name, now, now, now),
            )
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return self._public_user(row)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return self._public_user(row)

    def get_password_hash(self, user_id: str) -> str | None:
        with self._lock:
            row = self._execute(
                "SELECT password_hash FROM users WHERE user_id = ? AND is_active = 1", (user_id,)
            ).fetchone()
            return row["password_hash"] if row else None

    def update_profile(self, user_id: str, display_name: str) -> dict[str, Any] | None:
        with self._lock, self._transaction():
            self._execute(
                "UPDATE users SET display_name = ?, updated_at = ? WHERE user_id = ? AND is_active = 1",
                (display_name, self._now(), user_id),
            )
        return self.get_user(user_id)

    def change_password(self, user_id: str, password_hash: str, keep_session_id: str) -> None:
        now = self._now()
        with self._lock, self._transaction():
            self._execute(
                "UPDATE users SET password_hash = ?, password_changed_at = ?, updated_at = ? WHERE user_id = ?",
                (password_hash, now, now, user_id),
            )
            self._execute(
                "UPDATE auth_sessions SET revoked_at = ? WHERE user_id = ? AND session_id <> ? AND revoked_at IS NULL",
                (now, user_id, keep_session_id),
            )

    def create_auth_session(
        self,
        *,
        session_id: str,
        user_id: str,
        refresh_token_hash: str,
        csrf_token_hash: str,
        family_id: str,
        expires_at: str,
    ) -> None:
        now = self._now()
        with self._lock, self._transaction():
            self._execute(
                "INSERT INTO auth_sessions (session_id, user_id, refresh_token_hash, csrf_token_hash, "
                "family_id, expires_at, created_at, last_used_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    user_id,
                    refresh_token_hash,
                    csrf_token_hash,
                    family_id,
                    expires_at,
                    now,
                    now,
                ),
            )

    def rotate_auth_session(
        self,
        *,
        old_refresh_hash: str,
        new_session_id: str,
        new_refresh_hash: str,
        new_csrf_hash: str,
        new_expires_at: str,
        now: str,
    ) -> tuple[str, dict[str, Any] | None]:
        """Atomically rotate a refresh token; reused ancestors revoke the entire family."""
        with self._lock, self._transaction():
            query = (
                "SELECT s.*, u.is_active FROM auth_sessions s JOIN users u ON u.user_id = s.user_id "
                "WHERE s.refresh_token_hash = ?"
            )
            if self._connection.is_postgresql:
                query += " FOR UPDATE OF s"
            row = self._execute(query, (old_refresh_hash,)).fetchone()
            if row is None:
                return "invalid", None
            if row["rotated_at"] is not None:
                self._execute(
                    REVOKE_SESSION_FAMILY_SQL,
                    (now, row["family_id"]),
                )
                return "reuse", None
            if row["revoked_at"] is not None or row["expires_at"] <= now or not row["is_active"]:
                self._execute(
                    REVOKE_SESSION_FAMILY_SQL,
                    (now, row["family_id"]),
                )
                return "invalid", None
            updated = self._execute(
                "UPDATE auth_sessions SET rotated_at = ?, last_used_at = ? "
                "WHERE session_id = ? AND rotated_at IS NULL AND revoked_at IS NULL",
                (now, now, row["session_id"]),
            )
            if updated.rowcount != 1:
                self._execute(
                    REVOKE_SESSION_FAMILY_SQL,
                    (now, row["family_id"]),
                )
                return "reuse", None
            self._execute(
                "INSERT INTO auth_sessions (session_id, user_id, refresh_token_hash, csrf_token_hash, "
                "family_id, expires_at, created_at, last_used_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_session_id,
                    row["user_id"],
                    new_refresh_hash,
                    new_csrf_hash,
                    row["family_id"],
                    new_expires_at,
                    now,
                    now,
                ),
            )
            user = self._public_user(
                self._execute("SELECT * FROM users WHERE user_id = ?", (row["user_id"],)).fetchone()
            )
            return "rotated", {"user": user, "session_id": new_session_id}

    def get_active_auth_session(self, session_id: str, user_id: str, now: str) -> bool:
        with self._lock:
            row = self._execute(
                "SELECT 1 FROM auth_sessions s JOIN users u ON u.user_id = s.user_id "
                "WHERE s.session_id = ? AND s.user_id = ? AND s.revoked_at IS NULL AND s.rotated_at IS NULL "
                "AND s.expires_at > ? AND u.is_active = 1",
                (session_id, user_id, now),
            ).fetchone()
            return row is not None

    def get_csrf_hash(self, refresh_token_hash: str) -> str | None:
        with self._lock:
            row = self._execute(
                "SELECT csrf_token_hash FROM auth_sessions WHERE refresh_token_hash = ? "
                "AND revoked_at IS NULL AND rotated_at IS NULL",
                (refresh_token_hash,),
            ).fetchone()
            return row["csrf_token_hash"] if row else None

    def revoke_auth_session(self, session_id: str, user_id: str, now: str) -> None:
        with self._lock, self._transaction():
            self._execute(
                "UPDATE auth_sessions SET revoked_at = ? WHERE session_id = ? AND user_id = ? AND revoked_at IS NULL",
                (now, session_id, user_id),
            )

    def revoke_all_auth_sessions(
        self, user_id: str, now: str, except_session_id: str | None = None
    ) -> None:
        with self._lock, self._transaction():
            if except_session_id:
                self._execute(
                    "UPDATE auth_sessions SET revoked_at = ? WHERE user_id = ? AND session_id <> ? AND revoked_at IS NULL",
                    (now, user_id, except_session_id),
                )
            else:
                self._execute(
                    "UPDATE auth_sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                    (now, user_id),
                )

    def count_active_runs(self, owner_user_id: str) -> int:
        with self._lock:
            row = self._execute(
                "SELECT COUNT(*) AS count FROM runs WHERE owner_user_id = ? "
                "AND status IN ('CREATED', 'QUEUED', 'RUNNING', 'PLANNING', 'ANALYZING')",
                (owner_user_id,),
            ).fetchone()
            return int(row["count"])

    def auth_rate_limit_seconds(self, identifier_hash: str, now: str) -> int:
        with self._lock:
            row = self._execute(
                "SELECT blocked_until FROM auth_rate_limits WHERE identifier_hash = ?",
                (identifier_hash,),
            ).fetchone()
            if row is None or row["blocked_until"] is None or row["blocked_until"] <= now:
                return 0
            blocked_until = datetime.fromisoformat(row["blocked_until"].replace("Z", UTC_OFFSET))
            current = datetime.fromisoformat(now.replace("Z", UTC_OFFSET))
        return max(1, math.ceil((blocked_until - current).total_seconds()))

    def record_auth_failure(self, identifier_hash: str, now: str) -> None:
        with self._lock, self._transaction():
            row = self._execute(
                "SELECT failures FROM auth_rate_limits WHERE identifier_hash = ?",
                (identifier_hash,),
            ).fetchone()
            failures = int(row["failures"]) + 1 if row else 1
            cooldown_seconds = min(900, 30 * (2 ** min(failures - 5, 5))) if failures >= 5 else 0
            blocked_until = None
            if cooldown_seconds:
                blocked_until = (
                    (
                        datetime.fromisoformat(now.replace("Z", UTC_OFFSET))
                        + timedelta(seconds=cooldown_seconds)
                    )
                    .isoformat()
                    .replace(UTC_OFFSET, "Z")
                )
            self._execute(
                "INSERT INTO auth_rate_limits (identifier_hash, failures, blocked_until, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT (identifier_hash) DO UPDATE SET "
                "failures = excluded.failures, blocked_until = excluded.blocked_until, updated_at = excluded.updated_at",
                (identifier_hash, failures, blocked_until, now),
            )

    def login_rate_limit_seconds(self, identifier_hash: str, now: str) -> int:
        with self._lock:
            row = self._execute(
                "SELECT blocked_until FROM auth_login_limits WHERE identifier_hash = ?",
                (identifier_hash,),
            ).fetchone()
            if row is None or row["blocked_until"] is None or row["blocked_until"] <= now:
                return 0
            blocked_until = datetime.fromisoformat(row["blocked_until"].replace("Z", UTC_OFFSET))
            current = datetime.fromisoformat(now.replace("Z", UTC_OFFSET))
        return max(1, math.ceil((blocked_until - current).total_seconds()))

    def record_login_failure(self, identifier_hash: str, now: str) -> None:
        with self._lock, self._transaction():
            row = self._execute(
                "SELECT failures FROM auth_login_limits WHERE identifier_hash = ?",
                (identifier_hash,),
            ).fetchone()
            failures = int(row["failures"]) + 1 if row else 1
            cooldown = min(900, 30 * (2 ** min(failures - 5, 5))) if failures >= 5 else 0
            blocked_until = None
            if cooldown:
                blocked_until = (
                    (
                        datetime.fromisoformat(now.replace("Z", UTC_OFFSET))
                        + timedelta(seconds=cooldown)
                    )
                    .isoformat()
                    .replace(UTC_OFFSET, "Z")
                )
            self._execute(
                "INSERT INTO auth_login_limits (identifier_hash, failures, blocked_until, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT (identifier_hash) DO UPDATE SET "
                "failures = excluded.failures, blocked_until = excluded.blocked_until, updated_at = excluded.updated_at",
                (identifier_hash, failures, blocked_until, now),
            )

    def clear_login_failures(self, identifier_hash: str) -> None:
        with self._lock, self._transaction():
            self._execute(
                "DELETE FROM auth_login_limits WHERE identifier_hash = ?", (identifier_hash,)
            )

    def clear_auth_failures(self, identifier_hash: str) -> None:
        with self._lock, self._transaction():
            self._execute(
                "DELETE FROM auth_rate_limits WHERE identifier_hash = ?", (identifier_hash,)
            )
