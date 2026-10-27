"""Actual SQL concurrency plus explicitly synthetic network/clock cases."""

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from neurolab.auth import keyed_hash
from neurolab.rate_limits import (
    SharedRateLimiter,
    canonical_ip,
    request_peer_identity,
    trusted_networks,
)
from neurolab.store import RunStore
from tests.isolated_database import isolated_database


class SharedRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = isolated_database(self.temporary.name)
        self.path = self.database.__enter__()
        self.store = RunStore(self.path)
        self.limiter = SharedRateLimiter(self.store)

    def tearDown(self):
        self.store.close()
        self.database.__exit__(None, None, None)
        self.temporary.cleanup()

    def test_concurrent_replicas_cannot_exceed_shared_budget(self):
        barrier = threading.Barrier(6)

        def consume(_):
            store = RunStore(self.path)
            try:
                barrier.wait()
                with patch.object(store, "database_epoch", return_value=120):
                    return (
                        SharedRateLimiter(store)
                        .consume("test-account", "account:expensive", 3)
                        .allowed
                    )
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(consume, range(6)))
        self.assertEqual(sum(results), 3)
        with self.store._lock:
            row = self.store._execute("SELECT count FROM request_rate_buckets").fetchone()
        self.assertEqual(row["count"], 3)

    def test_window_boundary_retry_after_and_restart_are_database_driven(self):
        with patch.object(self.store, "database_epoch", return_value=59.2):
            self.assertTrue(self.limiter.consume("test", "peer:all", 1).allowed)
            denied = self.limiter.consume("test", "peer:all", 1)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.retry_after, 1)
        self.store.close()
        self.store = RunStore(self.path)
        self.limiter = SharedRateLimiter(self.store)
        with patch.object(self.store, "database_epoch", return_value=59.5):
            self.assertFalse(self.limiter.consume("test", "peer:all", 1).allowed)
        with patch.object(self.store, "database_epoch", return_value=60):
            self.assertTrue(self.limiter.consume("test", "peer:all", 1).allowed)

    def test_saturation_does_not_evict_live_buckets_or_reset_their_limits(self):
        limiter = SharedRateLimiter(self.store, max_buckets=1)
        with patch.object(self.store, "database_epoch", return_value=1):
            self.assertTrue(limiter.consume("existing", "peer:all", 1).allowed)
            denied = limiter.consume("new", "peer:all", 1)
            self.assertEqual(denied.reason, "capacity")
            self.assertEqual(denied.retry_after, 59)
            self.assertFalse(limiter.consume("existing", "peer:all", 1).allowed)
        with patch.object(self.store, "database_epoch", return_value=61):
            self.assertTrue(limiter.consume("new", "peer:all", 1).allowed)

    def test_only_keyed_digests_are_stored_and_namespaces_do_not_collide(self):
        self.limiter.consume("198.51.100.24", "peer:all", 1)
        self.limiter.consume("198.51.100.24", "account:all", 1)
        with self.store._lock:
            rows = [
                dict(r)
                for r in self.store._execute("SELECT * FROM request_rate_buckets").fetchall()
            ]
        self.assertNotIn("198.51.100.24", json.dumps(rows))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(len(r["bucket_key"]) == 64 for r in rows))
        self.assertNotEqual(rows[0]["bucket_key"], rows[1]["bucket_key"])

    def test_subject_and_account_limits_are_independent_of_peer_rotation(self):
        with patch.object(self.store, "database_epoch", return_value=120):
            for peer in ("198.51.100.1", "198.51.100.2"):
                self.assertTrue(self.limiter.consume(peer, "peer:expensive", 1).allowed)
            self.assertTrue(self.limiter.consume("verified-owner", "account:expensive", 1).allowed)
            self.assertFalse(self.limiter.consume("verified-owner", "account:expensive", 1).allowed)
            self.assertTrue(self.limiter.consume("different-owner", "account:expensive", 1).allowed)

    def test_parallel_login_failures_are_not_lost(self):
        barrier = threading.Barrier(6)
        key = keyed_hash("explicit synthetic login subject")

        def fail(_):
            store = RunStore(self.path)
            try:
                barrier.wait()
                store.record_login_failure(key, "2026-10-27T00:00:00Z")
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(fail, range(6)))
        with self.store._lock:
            row = self.store._execute(
                "SELECT failures FROM auth_login_limits WHERE identifier_hash=?", (key,)
            ).fetchone()
        self.assertEqual(row["failures"], 6)
        self.assertEqual(self.store.login_rate_limit_seconds(key, "2026-10-27T00:00:00Z"), 60)

    def test_invalid_limits_fail_before_mutation(self):
        with self.assertRaises(ValueError):
            SharedRateLimiter(self.store, max_buckets=0)
        with self.assertRaises(ValueError):
            self.limiter.consume("test", "peer:all", 0)
        with self.assertRaises(ValueError):
            self.limiter.consume("test", "peer:all", 1, window_seconds=0)


class ProxyIdentityTests(unittest.TestCase):
    def test_forwarded_identity_requires_both_trusted_network_and_service_credential(self):
        networks = trusted_networks("127.0.0.1/32,::1/128")
        headers = {
            b"x-neurolab-client-ip": b"198.51.100.20",
            b"x-neurolab-service-token": b"a" * 32,
        }
        self.assertEqual(
            request_peer_identity("127.0.0.1", headers, "a" * 32, networks), "198.51.100.20"
        )
        self.assertEqual(
            request_peer_identity("203.0.113.1", headers, "a" * 32, networks), "203.0.113.1"
        )
        self.assertEqual(
            request_peer_identity("127.0.0.1", headers, "b" * 32, networks), "127.0.0.1"
        )
        self.assertEqual(request_peer_identity("127.0.0.1", headers, "", networks), "127.0.0.1")
        invalid = {**headers, b"x-neurolab-client-ip": b"198.51.100.20, 198.51.100.21"}
        self.assertEqual(
            request_peer_identity("127.0.0.1", invalid, "a" * 32, networks), "127.0.0.1"
        )

    def test_canonical_addresses_and_explicit_proxy_configuration(self):
        self.assertEqual(canonical_ip("::ffff:198.51.100.1"), "198.51.100.1")
        self.assertEqual(canonical_ip("2001:0DB8::1"), "2001:db8::1")
        self.assertIsNone(canonical_ip("fe80::1%random-zone"))
        self.assertIsNone(canonical_ip("not an IP"))
        self.assertIsNone(canonical_ip(None))
        with self.assertRaises(ValueError):
            trusted_networks("0.0.0.0/0")
        with self.assertRaises(ValueError):
            trusted_networks("")


class SharedMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = RunStore(":memory:")

    def tearDown(self):
        self.store.close()

    async def invoke(
        self,
        middleware,
        *,
        peer="127.0.0.1",
        forwarded="198.51.100.1",
        service_credential="a" * 32,
        path="/datasets",
    ):
        sent = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "scheme": "http",
            "client": (peer, 1234),
            "headers": [
                (b"x-neurolab-service-token", service_credential.encode()),
                (b"x-neurolab-client-ip", forwarded.encode()),
            ],
        }
        await middleware(scope, receive, send)
        return (
            sent[0]["status"],
            dict(sent[0]["headers"]),
            b"".join(m.get("body", b"") for m in sent),
        )

    async def test_instances_share_budgets_and_proxy_headers_cannot_bypass_trust(self):
        from neurolab.api import RequestSecurityMiddleware

        async def ok(scope, receive, send):
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        service_credential = "a" * 32
        replicas = [
            RequestSecurityMiddleware(
                ok,
                rate_store=self.store,
                require_auth=True,
                bearer_token=service_credential,
                requests_per_minute=1,
            )
            for _ in range(2)
        ]
        with patch.object(self.store, "database_epoch", return_value=120):
            self.assertEqual((await self.invoke(replicas[0]))[0], 204)
            status, headers, _ = await self.invoke(replicas[1])
            self.assertEqual(status, 429)
            self.assertEqual(headers[b"retry-after"], b"60")
            self.assertEqual((await self.invoke(replicas[1], forwarded="198.51.100.2"))[0], 204)
            self.assertEqual((await self.invoke(replicas[0], peer="203.0.113.3"))[0], 204)
            self.assertEqual(
                (await self.invoke(replicas[1], peer="203.0.113.3", forwarded="198.51.100.4"))[0],
                429,
            )
            self.assertEqual((await self.invoke(replicas[1], service_credential="wrong"))[0], 401)

    async def test_store_outage_fails_closed_without_leaking_details_and_health_is_liveness(self):
        from neurolab.api import RequestSecurityMiddleware

        async def ok(scope, receive, send):
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = RequestSecurityMiddleware(ok, rate_store=self.store, require_auth=False)
        with patch.object(
            middleware.limiter, "consume", side_effect=RuntimeError("private database credential")
        ):
            status, headers, body = await self.invoke(middleware)
            self.assertEqual(status, 503)
            self.assertEqual(headers[b"retry-after"], b"1")
            self.assertNotIn(b"private database credential", body)
            self.assertEqual((await self.invoke(middleware, path="/health"))[0], 204)
