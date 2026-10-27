"""Durable SQL queue consumer: python -m neurolab.worker [--once]."""

from __future__ import annotations

import argparse
import logging
import os
import signal
import threading
import uuid
from pathlib import Path

from .jobs import ResearchJobs
from .research_context import ResearchRunRequest
from .store import ExecutionLeaseLost

LOGGER = logging.getLogger(__name__)


class QueueWorker:
    def __init__(self, store, executor, *, lease_seconds=30, max_running=2):
        if not 1 <= lease_seconds <= 120 or max_running < 1:
            raise ValueError("Invalid worker settings")
        self.store, self.executor = store, executor
        self.jobs = ResearchJobs(store)
        self.lease_seconds, self.max_running = lease_seconds, max_running
        self.worker_id = str(uuid.uuid4())

    def _heartbeat(self, stop, claim):
        interval = min(5, self.lease_seconds / 3)
        while not stop.wait(interval):
            try:
                if not self.jobs.renew(
                    claim["run_id"], claim["token"], lease_seconds=self.lease_seconds
                ):
                    self.jobs.reconcile()
                    break
            except Exception:
                # Transient DB outages cannot extend a lease; all subsequent
                # writes/provider calls recheck ownership and expiration.
                LOGGER.warning("Worker lease renewal unavailable; no lease extension assumed")

    def run_once(self, *, run_id=None):
        claim = self.jobs.claim(
            self.worker_id,
            run_id=run_id,
            lease_seconds=self.lease_seconds,
            max_running=self.max_running,
        )
        if claim is None:
            return False
        stop = threading.Event()
        heartbeat = threading.Thread(target=self._heartbeat, args=(stop, claim), daemon=True)
        heartbeat.start()
        try:
            with self.store.execution_lease(claim["run_id"], claim["token"]):
                try:
                    self.executor(
                        ResearchRunRequest.model_validate(claim["request"]), claim["run_id"]
                    )
                except ExecutionLeaseLost:
                    raise
                except Exception as error:
                    self.store.add_event(
                        claim["run_id"],
                        "run.failed",
                        {
                            "error_type": type(error).__name__,
                            "message": "Worker execution failed; completed artifacts are retained.",
                            "retryable": False,
                        },
                    )
        except ExecutionLeaseLost:
            LOGGER.warning("Worker execution lease lost; stale writes rejected")
        finally:
            stop.set()
            heartbeat.join(timeout=2)
        self.jobs.finish(claim["run_id"], claim["token"])
        return True

    def drain(self):
        completed = 0
        while self.run_once():
            completed += 1
        return completed


def poll_queue(worker, stop, *, once=False, poll_seconds=1):
    while not stop.is_set():
        worked = worker.run_once()
        if once:
            break
        if not worked:
            stop.wait(poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=1)
    args = parser.parse_args()
    if not 0.1 <= args.poll_seconds <= 30:
        parser.error("poll-seconds must be between 0.1 and 30")
    # No HTTP app or JWT signing key is imported into the worker process.
    from .execution import execute_run
    from .ghana import load_ghana
    from .store import RunStore

    store = RunStore(os.getenv("DATABASE_URL", "postgresql:///neurolab"))
    dataset = load_ghana(Path(__file__).resolve().parents[1])
    worker = QueueWorker(
        store,
        lambda request, run_id: execute_run(store, dataset, request, run_id),
        max_running=int(os.getenv("RESEARCH_MAX_RUNNING_JOBS", "2")),
    )
    stop = threading.Event()
    previous = {
        name: signal.signal(name, lambda _signum, _frame: stop.set())
        for name in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        poll_queue(worker, stop, once=args.once, poll_seconds=args.poll_seconds)
    finally:
        for name, handler in previous.items():
            signal.signal(name, handler)
        store.close()


if __name__ == "__main__":
    main()
