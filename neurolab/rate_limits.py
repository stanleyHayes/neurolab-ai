"""Database-time shared request limits and explicit proxy identity trust."""

from __future__ import annotations

import hmac
import ipaddress
import math
from dataclasses import dataclass

from .auth import keyed_hash


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after: int = 0
    reason: str = "allowed"


class SharedRateLimiter:
    def __init__(self, store, *, max_buckets=10_000):
        if not 1 <= max_buckets <= 100_000:
            raise ValueError("Invalid shared rate bucket capacity")
        self.store, self.max_buckets = store, max_buckets

    def consume(self, identity, namespace, limit, *, window_seconds=60):
        if not 1 <= limit <= 1_000_000 or not 1 <= window_seconds <= 3600:
            raise ValueError("Invalid rate limit or window")
        key = keyed_hash("rate:v1:" + namespace + ":" + identity)
        with self.store.atomic():
            self.store._execute(
                "UPDATE request_rate_control SET revision=revision+1 WHERE control_id=1"
            )
            now = self.store.database_epoch()
            self.store._execute("DELETE FROM request_rate_buckets WHERE window_end <= ?", (now,))
            row = self.store._execute(
                "SELECT count, window_end FROM request_rate_buckets WHERE bucket_key=?", (key,)
            ).fetchone()
            if row:
                if row["count"] >= limit:
                    return RateDecision(False, max(1, math.ceil(row["window_end"] - now)), "limit")
                self.store._execute(
                    "UPDATE request_rate_buckets SET count=count+1 WHERE bucket_key=?", (key,)
                )
            else:
                size = self.store._execute(
                    "SELECT COUNT(*) AS n FROM request_rate_buckets"
                ).fetchone()["n"]
                if size >= self.max_buckets:
                    first = self.store._execute(
                        "SELECT MIN(window_end) AS expiry FROM request_rate_buckets"
                    ).fetchone()["expiry"]
                    return RateDecision(False, max(1, math.ceil(first - now)), "capacity")
                end = (math.floor(now / window_seconds) + 1) * window_seconds
                self.store._execute(
                    "INSERT INTO request_rate_buckets (bucket_key,count,window_end) VALUES (?,1,?)",
                    (key, end),
                )
            return RateDecision(True)


def canonical_ip(value):
    if not isinstance(value, str) or "%" in value or len(value) > 45:
        return None
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    mapped = getattr(address, "ipv4_mapped", None)
    return str(mapped or address)


def trusted_networks(value):
    networks = tuple(
        ipaddress.ip_network(item.strip(), strict=True) for item in value.split(",") if item.strip()
    )
    if not networks or any(network.prefixlen == 0 for network in networks):
        raise ValueError("Trusted proxy networks must be explicit, non-wildcard CIDRs")
    return networks


def request_peer_identity(peer, headers, service_token, networks):
    actual = canonical_ip(peer)
    identity = actual or "unknown"
    credential = headers.get(b"x-neurolab-service-token", b"").decode("latin-1", errors="ignore")
    valid_service = len(service_token) >= 32 and hmac.compare_digest(credential, service_token)
    if (
        actual
        and valid_service
        and any(ipaddress.ip_address(actual) in network for network in networks)
    ):
        forwarded = headers.get(b"x-neurolab-client-ip", b"").decode("latin-1", errors="ignore")
        return canonical_ip(forwarded) or identity
    return identity
