"""Server-side rate limiting for the ANONYMOUS AI exploration funnel.

SECURITY / COST: the anonymous funnel (research -> opportunities -> positioning
-> transformation) runs real AI without consuming user credits so visitors can
explore before signing up. That is an owner-side cost and abuse vector, so every
anonymous AI request is rate-limited HERE, server-side, keyed by client IP.

The frontend is NEVER trusted: there are no client counters involved in the
decision. Limits are configurable via environment variables (no scattered magic
numbers). Authenticated users do NOT pass through this module at all — they use
the existing plan / credit / entitlement system.
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta

from db import db

logger = logging.getLogger("khova.ratelimit")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# CONFIG (env-driven — see backend/.env)
# ---------------------------------------------------------------------------
def limits() -> dict:
    """Return the current, live rate-limit configuration (read each call so
    env changes take effect without code edits)."""
    return {
        "max_requests": _int_env("KHOVA_ANON_MAX_AI", 8),
        "window_sec": _int_env("KHOVA_ANON_WINDOW_SEC", 3600),
        "min_interval_sec": _int_env("KHOVA_ANON_MIN_INTERVAL_SEC", 3),
        "cooldown_sec": _int_env("KHOVA_ANON_COOLDOWN_SEC", 600),
        "dedup_sec": _int_env("KHOVA_ANON_DEDUP_SEC", 30),
    }


# User-facing messages (localized-friendly, short).
MSG_LIMIT = "You've reached the free exploration limit. Please sign in to continue."
MSG_COOLDOWN = "You've reached the free exploration limit. Please sign in to continue, or try again shortly."
MSG_TOO_FAST = "You're going a little fast. Please wait a moment and try again."
MSG_DUPLICATE = "This request is already being processed. Please wait for it to finish."


class AnonRateLimited(Exception):
    """Raised when an anonymous AI request must be blocked."""
    def __init__(self, reason: str, message: str, retry_after: int = 0, remaining: int = 0):
        self.reason = reason           # limit | cooldown | too_fast | duplicate
        self.message = message
        self.retry_after = int(retry_after or 0)
        self.remaining = int(remaining or 0)
        super().__init__(f"anon_rate_limited:{reason}")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def client_ip(request) -> str:
    """Resolve the real client IP, honouring the Kubernetes ingress proxy.
    Never trusts a body/header the client could freely spoof for identity —
    X-Forwarded-For is set by the ingress and is the best available signal."""
    if request is None:
        return "unknown"
    try:
        xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
        if xff:
            first = xff.split(",")[0].strip()
            if first:
                return first
        xri = request.headers.get("x-real-ip")
        if xri:
            return xri.strip()
        if request.client and request.client.host:
            return request.client.host
    except Exception:
        pass
    return "unknown"


async def ensure_indexes():
    """Create supporting indexes (idempotent). A TTL index auto-expires old
    usage records so the collection cannot grow unbounded."""
    try:
        cfg = limits()
        ttl = max(cfg["window_sec"] * 2, cfg["cooldown_sec"] * 2, 3600)
        await db.anon_ai_usage.create_index("at", expireAfterSeconds=ttl)
        await db.anon_ai_usage.create_index([("ip", 1), ("at", -1)])
        await db.anon_blocks.create_index("ip", unique=True)
        await db.anon_blocks.create_index("blocked_until", expireAfterSeconds=ttl)
        logger.info("anon rate-limit indexes ensured (ttl=%ss)", ttl)
    except Exception as e:  # non-fatal: limiter still works without indexes
        logger.warning("ratelimit ensure_indexes failed (non-fatal): %s", e)


async def enforce_anon(request, task: str, project_id: str) -> dict:
    """Enforce the anonymous AI rate limit for one request.

    Raises AnonRateLimited on any block. On success records the request and
    returns {ip, remaining}. Order of checks: active cooldown -> rapid-fire ->
    duplicate/simultaneous -> rolling-window count.
    """
    cfg = limits()
    ip = client_ip(request)
    now = _now()

    # 1) Active cooldown block?
    blk = await db.anon_blocks.find_one({"ip": ip})
    if blk and blk.get("blocked_until"):
        bu = blk["blocked_until"]
        if isinstance(bu, str):
            try:
                bu = datetime.fromisoformat(bu)
            except ValueError:
                bu = None
        if bu is not None:
            if bu.tzinfo is None:
                bu = bu.replace(tzinfo=timezone.utc)
            if bu > now:
                raise AnonRateLimited("cooldown", MSG_COOLDOWN,
                                      retry_after=int((bu - now).total_seconds()))

    # 2) Rapid-fire guard (any task, same IP).
    last = await db.anon_ai_usage.find_one({"ip": ip}, sort=[("at", -1)])
    if last and last.get("at"):
        la = last["at"]
        if la.tzinfo is None:
            la = la.replace(tzinfo=timezone.utc)
        gap = (now - la).total_seconds()
        if gap < cfg["min_interval_sec"]:
            raise AnonRateLimited("too_fast", MSG_TOO_FAST,
                                  retry_after=max(1, int(cfg["min_interval_sec"] - gap)))

    # 3) Duplicate / simultaneous flood (same task+project) within dedup window.
    dedup_cut = now - timedelta(seconds=cfg["dedup_sec"])
    dup = await db.anon_ai_usage.find_one({
        "ip": ip, "task": task, "project_id": project_id, "at": {"$gte": dedup_cut},
    })
    if dup:
        raise AnonRateLimited("duplicate", MSG_DUPLICATE, retry_after=cfg["dedup_sec"])

    # 4) Rolling-window count.
    win_cut = now - timedelta(seconds=cfg["window_sec"])
    count = await db.anon_ai_usage.count_documents({"ip": ip, "at": {"$gte": win_cut}})
    if count >= cfg["max_requests"]:
        # Apply a cooldown so repeated probing keeps getting blocked cheaply.
        until = now + timedelta(seconds=cfg["cooldown_sec"])
        await db.anon_blocks.update_one(
            {"ip": ip},
            {"$set": {"ip": ip, "blocked_until": until, "reason": "window_exceeded", "at": now}},
            upsert=True,
        )
        raise AnonRateLimited("limit", MSG_LIMIT, retry_after=cfg["cooldown_sec"])

    # 5) Record the request (also acts as the in-flight/rapid marker).
    await db.anon_ai_usage.insert_one({
        "id": f"anon_{uuid.uuid4().hex[:12]}",
        "ip": ip, "task": task, "project_id": project_id, "at": now,
    })
    return {"ip": ip, "remaining": max(0, cfg["max_requests"] - count - 1)}
