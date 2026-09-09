"""Generation job system for Khova AI.

Every expensive AI operation runs inside a tracked job with a clear lifecycle
(RUNNING -> COMPLETED | FAILED). Credits are reserved-then-charged: they are only
deducted on successful completion, so a job that fails before meaningful
completion costs the user nothing (safe refund-by-design). The system also
prevents accidental duplicate concurrent generation and caps retries.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta

from db import db
import billing
import model_router

logger = logging.getLogger("khova.jobs")

DEDUP_WINDOW_SEC = 90
RETRY_WINDOW_MIN = 10
MAX_RETRIES = 3


def now():
    return datetime.now(timezone.utc)


def now_iso():
    return now().isoformat()


# --- Domain exceptions (mapped to HTTP status in server.py) ----------------
class FeatureLocked(Exception):
    def __init__(self, feature):
        self.feature = feature
        super().__init__(f"feature_locked:{feature}")


class InsufficientCredits(Exception):
    def __init__(self, needed, balance):
        self.needed = needed
        self.balance = balance
        super().__init__("insufficient_credits")


class CreationLimitReached(Exception):
    pass


class DuplicateJob(Exception):
    pass


class RetryLimitReached(Exception):
    pass


async def _recent_running(user_id, project_id, task):
    cutoff = (now() - timedelta(seconds=DEDUP_WINDOW_SEC)).isoformat()
    return await db.generation_jobs.find_one({
        "user_id": user_id, "project_id": project_id, "task": task,
        "status": "running", "started_at": {"$gte": cutoff},
    })


async def _recent_failures(user_id, project_id, task):
    cutoff = (now() - timedelta(minutes=RETRY_WINDOW_MIN)).isoformat()
    return await db.generation_jobs.count_documents({
        "user_id": user_id, "project_id": project_id, "task": task,
        "status": "failed", "completed_at": {"$gte": cutoff},
    })


async def begin(user: dict, proj: dict, task: str) -> dict:
    """Validate entitlement + credits, create a RUNNING job. Raises domain
    exceptions on any block. Does NOT deduct credits yet (charged on complete).

    Admin/developer accounts bypass entitlement/credit gates (still tracked)."""
    user_id = user["user_id"]
    project_id = proj["id"]
    cost = billing.task_cost(task)
    is_admin = (user.get("role") == "admin")

    if not is_admin:
        # 1) Feature entitlement
        feat = billing.TASK_FEATURE.get(task)
        if feat and not billing.feature_enabled(user, feat):
            raise FeatureLocked(feat)

        # 2) Free-tier creation limit (only for a NOT-yet-counted new product)
        if task in billing.CREATION_TASKS and not proj.get("counted_as_creation"):
            if not billing.creation_allowed(user):
                raise CreationLimitReached()

        # 3) Retry protection
        if await _recent_failures(user_id, project_id, task) >= MAX_RETRIES:
            raise RetryLimitReached()

        # 4) Duplicate concurrent job protection (idempotency)
        if await _recent_running(user_id, project_id, task):
            raise DuplicateJob()

        # 5) Credit sufficiency (checked now, charged on success)
        if cost > 0 and not await billing.can_afford(user_id, cost):
            raise InsufficientCredits(cost, await billing.get_balance(user_id))

    routing = model_router.route(task)
    job = {
        "id": f"job_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "project_id": project_id,
        "task": task,
        "tier": routing["tier"],
        "provider": routing["provider"],
        "model": routing["model"],
        "estimated_credits": cost,
        "credits_charged": 0,
        "status": "running",
        "retry_count": 0,
        "error": None,
        "started_at": now_iso(),
        "completed_at": None,
        "created_at": now_iso(),
    }
    await db.generation_jobs.insert_one(dict(job))
    return job


async def complete(user: dict, proj: dict, job: dict) -> dict:
    """Charge credits atomically and mark the job COMPLETED. Increments the
    free-tier creation counter the first time a product creation task succeeds.

    Returns {balance, cost, counted_creation}. If the atomic deduction fails
    (e.g. a concurrent spend drained the balance), the job is marked FAILED and
    InsufficientCredits is raised — the user is never charged partially."""
    task = job["task"]
    cost = billing.task_cost(task)
    balance = await billing.get_balance(user["user_id"])
    is_admin = (user.get("role") == "admin")

    if cost > 0 and not is_admin:
        try:
            balance = await billing.deduct_credits(
                user["user_id"], cost, reason=f"job:{task}", task=task, job_id=job["id"],
            )
        except ValueError:
            await fail(job, "insufficient_credits_at_completion")
            raise InsufficientCredits(cost, await billing.get_balance(user["user_id"]))

    counted_creation = False
    if not is_admin and task in billing.CREATION_TASKS and not proj.get("counted_as_creation"):
        await billing.increment_creations(user["user_id"])
        counted_creation = True

    charged = 0 if is_admin else cost
    await db.generation_jobs.update_one(
        {"id": job["id"]},
        {"$set": {"status": "completed", "credits_charged": charged,
                  "balance_after": balance, "completed_at": now_iso()}},
    )
    job["status"] = "completed"
    job["credits_charged"] = charged
    return {"balance": balance, "cost": charged, "counted_creation": counted_creation}


async def fail(job: dict, error: str) -> None:
    await db.generation_jobs.update_one(
        {"id": job["id"]},
        {"$set": {"status": "failed", "error": str(error)[:500], "completed_at": now_iso()},
         "$inc": {"retry_count": 1}},
    )
    job["status"] = "failed"
