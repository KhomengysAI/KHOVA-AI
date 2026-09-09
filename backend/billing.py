"""Server-side economy for Khova AI: plans, entitlements, credit ledger,
redeem codes and usage logging.

SECURITY: the frontend is NEVER trusted for plan / credits / feature access.
Every entitlement decision and every credit mutation happens here, server-side,
and credit changes are atomic (conditional Mongo updates) so a balance can never
go negative and a deduction can never be duplicated or bypassed.
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta

from pymongo import ReturnDocument

from db import db

logger = logging.getLogger("khova.billing")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# PLANS (configurable — commercial pricing intentionally NOT hard-coded)
# ---------------------------------------------------------------------------
PLANS = {
    "free": {
        "name": "Free",
        "start_credits": 100,
        "max_creations": 3,          # lifetime free full-product creations
        "features": {
            "export": True,
            "bonus_generation": True,
            "visual_generation": True,
            "website_publish": False,
            "advanced_qa": False,
        },
        "limits": {
            "research_depth": "basic",
            "max_opportunities": 8,
            "max_chapters": 5,
            "max_visuals": 2,
            "max_regenerations": 5,
        },
    },
    "creator": {
        "name": "Creator",
        "start_credits": 1000,
        "max_creations": None,       # unlimited (subject to credits)
        "features": {
            "export": True,
            "bonus_generation": True,
            "visual_generation": True,
            "website_publish": True,
            "advanced_qa": True,
        },
        "limits": {
            "research_depth": "standard",
            "max_opportunities": 20,
            "max_chapters": 10,
            "max_visuals": 6,
            "max_regenerations": 30,
        },
    },
    "pro": {
        "name": "Pro",
        "start_credits": 5000,
        "max_creations": None,
        "features": {
            "export": True,
            "bonus_generation": True,
            "visual_generation": True,
            "website_publish": True,
            "advanced_qa": True,
        },
        "limits": {
            "research_depth": "deep",
            "max_opportunities": 30,
            "max_chapters": 16,
            "max_visuals": 12,
            "max_regenerations": 100,
        },
    },
}

DEFAULT_PLAN = "free"


# ---------------------------------------------------------------------------
# CREDIT COST per AI task (deterministic ops cost 0 — never charged)
# The discovery/exploration funnel (research, opportunities, positioning,
# transformation) is intentionally FREE so users can explore before committing;
# real credits are spent on PRODUCT GENERATION. The free-tier "3 creations"
# counter is the primary gate for that funnel-to-product step.
# ---------------------------------------------------------------------------
TASK_COSTS = {
    "research": 0,
    "opportunities": 0,
    "positioning": 0,
    "transformation": 0,
    "ebook_plan": 2,
    "ebook_section": 2,
    "ebook_intro": 1,
    "ebook_rewrite": 1,
    "cover": 4,
    "illustration": 4,
    "qa": 2,
    "qa_apply": 2,
    "branding": 1,
    "spreadsheet_spec": 2,
    "website_spec": 2,
    "website_section": 1,
    "bonus": 2,
}

# Tasks that count as starting a brand-new product "creation" (free-tier gate).
CREATION_TASKS = {"ebook_plan", "spreadsheet_spec", "website_spec"}

# Task -> required feature entitlement.
TASK_FEATURE = {
    "cover": "visual_generation",
    "illustration": "visual_generation",
    "bonus": "bonus_generation",
    "website_publish": "website_publish",
}


def task_cost(task: str) -> int:
    return int(TASK_COSTS.get(task, 0))


def plan_def(plan: str) -> dict:
    return PLANS.get(plan or DEFAULT_PLAN, PLANS[DEFAULT_PLAN])


# ---------------------------------------------------------------------------
# ADMIN role resolution
# ---------------------------------------------------------------------------
def admin_emails() -> set:
    raw = os.environ.get("KHOVA_ADMIN_EMAILS", "admin@khova.ai")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def resolve_role(email: str) -> str:
    return "admin" if (email or "").lower() in admin_emails() else "user"


# ---------------------------------------------------------------------------
# USER ECONOMY backfill / read
# ---------------------------------------------------------------------------
async def ensure_user_economy(user: dict) -> dict:
    """Backfill economy fields for existing users and return the fresh doc."""
    if not user:
        return user
    updates = {}
    if not user.get("plan"):
        updates["plan"] = DEFAULT_PLAN
    if user.get("credits") is None:
        updates["credits"] = plan_def(user.get("plan") or DEFAULT_PLAN)["start_credits"]
    if user.get("creations_used") is None:
        updates["creations_used"] = 0
    role = resolve_role(user.get("email", ""))
    if user.get("role") != role:
        updates["role"] = role
    if updates:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": updates})
        user.update(updates)
    return user


def economy_view(user: dict) -> dict:
    plan = user.get("plan") or DEFAULT_PLAN
    pdef = plan_def(plan)
    max_creations = pdef.get("max_creations")
    used = int(user.get("creations_used") or 0)
    remaining = None if max_creations is None else max(0, max_creations - used)
    return {
        "plan": plan,
        "plan_name": pdef["name"],
        "credits": int(user.get("credits") or 0),
        "role": user.get("role") or "user",
        "creations_used": used,
        "creations_remaining": remaining,
        "features": pdef["features"],
        "limits": pdef["limits"],
    }


def feature_enabled(user: dict, feature: str) -> bool:
    pdef = plan_def(user.get("plan") or DEFAULT_PLAN)
    return bool(pdef["features"].get(feature, False))


def plan_limit(user: dict, key: str):
    pdef = plan_def(user.get("plan") or DEFAULT_PLAN)
    return pdef["limits"].get(key)


# ---------------------------------------------------------------------------
# CREDIT LEDGER (atomic)
# ---------------------------------------------------------------------------
async def _ledger(user_id: str, delta: int, reason: str, balance_after: int, task: str = None, job_id: str = None):
    await db.credit_ledger.insert_one({
        "id": f"led_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "delta": delta,
        "reason": reason,
        "task": task,
        "job_id": job_id,
        "balance_after": balance_after,
        "created_at": now_iso(),
    })


async def get_balance(user_id: str) -> int:
    u = await db.users.find_one({"user_id": user_id}, {"credits": 1})
    return int((u or {}).get("credits") or 0)


async def can_afford(user_id: str, amount: int) -> bool:
    if amount <= 0:
        return True
    return (await get_balance(user_id)) >= amount


async def deduct_credits(user_id: str, amount: int, reason: str, task: str = None, job_id: str = None) -> int:
    """Atomically deduct credits. Returns new balance. Raises ValueError if insufficient.
    The conditional filter (credits >= amount) guarantees no negative balance and
    no double-spend under concurrency."""
    if amount <= 0:
        return await get_balance(user_id)
    doc = await db.users.find_one_and_update(
        {"user_id": user_id, "credits": {"$gte": amount}},
        {"$inc": {"credits": -amount}},
        projection={"credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise ValueError("insufficient_credits")
    new_balance = int(doc["credits"])
    await _ledger(user_id, -amount, reason, new_balance, task, job_id)
    return new_balance


async def grant_credits(user_id: str, amount: int, reason: str) -> int:
    if amount <= 0:
        return await get_balance(user_id)
    doc = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"credits": amount}},
        projection={"credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    new_balance = int((doc or {}).get("credits") or amount)
    await _ledger(user_id, amount, reason, new_balance)
    return new_balance


async def refund_credits(user_id: str, amount: int, reason: str, job_id: str = None) -> int:
    if amount <= 0:
        return await get_balance(user_id)
    doc = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"credits": amount}},
        projection={"credits": 1},
        return_document=ReturnDocument.AFTER,
    )
    new_balance = int((doc or {}).get("credits") or amount)
    await _ledger(user_id, amount, f"refund: {reason}", new_balance, job_id=job_id)
    return new_balance


# ---------------------------------------------------------------------------
# CREATIONS (free-tier)
# ---------------------------------------------------------------------------
async def increment_creations(user_id: str) -> int:
    doc = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"creations_used": 1}},
        projection={"creations_used": 1},
        return_document=ReturnDocument.AFTER,
    )
    return int((doc or {}).get("creations_used") or 1)


def creation_allowed(user: dict) -> bool:
    pdef = plan_def(user.get("plan") or DEFAULT_PLAN)
    mx = pdef.get("max_creations")
    if mx is None:
        return True
    return int(user.get("creations_used") or 0) < mx


# ---------------------------------------------------------------------------
# REDEEM CODES
# ---------------------------------------------------------------------------
async def create_redeem_code(admin_user: dict, plan: str = None, credits: int = 0,
                             max_redemptions: int = 1, expires_days=None, prefix: str = "KHOVA") -> dict:
    if plan and plan not in PLANS:
        raise ValueError("invalid_plan")
    code = f"{(prefix or 'KHOVA').upper().strip('-')}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    expires_at = None
    if expires_days:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=int(expires_days))).isoformat()
    doc = {
        "id": f"code_{uuid.uuid4().hex[:10]}",
        "code": code,
        "plan": plan,
        "credits": int(credits or 0),
        "max_redemptions": int(max_redemptions or 1),
        "redemptions": 0,
        "expires_at": expires_at,
        "active": True,
        "created_by": admin_user.get("user_id"),
        "created_at": now_iso(),
    }
    await db.redeem_codes.insert_one(dict(doc))
    doc.pop("_id", None)
    return doc


async def redeem_code(user: dict, code: str) -> dict:
    """Validate + apply a redeem code server-side. Returns a result dict.
    Raises ValueError with a machine reason on failure."""
    code = (code or "").strip().upper()
    if not code:
        raise ValueError("empty_code")
    doc = await db.redeem_codes.find_one({"code": code}, {"_id": 0})
    if not doc:
        raise ValueError("code_not_found")
    if not doc.get("active", True):
        raise ValueError("code_inactive")
    # expiry
    exp = doc.get("expires_at")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if exp_dt < datetime.now(timezone.utc):
                raise ValueError("code_expired")
        except ValueError as e:
            if str(e) == "code_expired":
                raise
    # redemption limit
    if int(doc.get("redemptions", 0)) >= int(doc.get("max_redemptions", 1)):
        raise ValueError("code_exhausted")
    # already redeemed by this user
    prior = await db.redemptions_log.find_one({"code": code, "user_id": user["user_id"]})
    if prior:
        raise ValueError("already_redeemed")

    # Atomically bump redemption count (guards concurrent exhaustion).
    updated = await db.redeem_codes.find_one_and_update(
        {"code": code, "redemptions": {"$lt": int(doc.get("max_redemptions", 1))}, "active": True},
        {"$inc": {"redemptions": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise ValueError("code_exhausted")

    granted_plan = doc.get("plan")
    granted_credits = int(doc.get("credits") or 0)
    set_fields = {}
    if granted_plan:
        set_fields["plan"] = granted_plan
    if set_fields:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": set_fields})
    balance = await get_balance(user["user_id"])
    if granted_credits:
        balance = await grant_credits(user["user_id"], granted_credits, f"redeem:{code}")

    await db.redemptions_log.insert_one({
        "id": f"rd_{uuid.uuid4().hex[:10]}",
        "code": code,
        "user_id": user["user_id"],
        "plan": granted_plan,
        "credits": granted_credits,
        "at": now_iso(),
    })
    # deactivate single-use codes once exhausted
    if int(updated.get("redemptions", 0)) >= int(updated.get("max_redemptions", 1)):
        await db.redeem_codes.update_one({"code": code}, {"$set": {"active": False}})

    return {
        "ok": True,
        "code": code,
        "plan_granted": granted_plan,
        "credits_granted": granted_credits,
        "balance": balance,
    }


REDEEM_MESSAGES = {
    "empty_code": "Please enter a code.",
    "code_not_found": "This code is not valid.",
    "code_inactive": "This code is no longer active.",
    "code_expired": "This code has expired.",
    "code_exhausted": "This code has reached its redemption limit.",
    "already_redeemed": "You have already redeemed this code.",
    "invalid_plan": "The code refers to an unknown plan.",
}
