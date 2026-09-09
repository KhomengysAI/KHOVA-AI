"""Khova AI — FastAPI backend. AI digital product factory pipeline."""
import os
import io
import uuid
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import db, serialize_doc, GENERATED_DIR
from auth import auth_router, get_current_user, get_optional_user
import agents
import exporters
import billing
import jobs
import model_router
import ratelimit
from llm_service import DEFAULT_MODELS, generate_image
from agents import build_cover_prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("khova")

app = FastAPI(title="Khova AI")
api = APIRouter(prefix="/api")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Admin dependency
# ---------------------------------------------------------------------------
async def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    if (user or {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Generation-job orchestration
# ---------------------------------------------------------------------------
def _job_http(exc):
    """Map domain job exceptions to HTTP responses."""
    if isinstance(exc, jobs.FeatureLocked):
        raise HTTPException(status_code=403, detail="This feature isn't available on your current plan. Upgrade or redeem a code to unlock it.")
    if isinstance(exc, jobs.InsufficientCredits):
        raise HTTPException(status_code=402, detail=f"Not enough credits — this needs {exc.needed}, you have {exc.balance}. Redeem a code or upgrade your plan.")
    if isinstance(exc, jobs.CreationLimitReached):
        raise HTTPException(status_code=402, detail="You've reached your free creation limit. Redeem a code or upgrade to keep creating.")
    if isinstance(exc, jobs.DuplicateJob):
        raise HTTPException(status_code=409, detail="This generation is already running. Please wait for it to finish.")
    if isinstance(exc, jobs.RetryLimitReached):
        raise HTTPException(status_code=429, detail="Too many failed attempts for this step. Please try again in a few minutes.")
    raise exc


async def run_ai(user: Optional[dict], proj: dict, task: str, coro_factory, request: Optional[Request] = None):
    """Run an AI generation inside a tracked job.

    - Authenticated: full entitlement + credit check (reserve → charge on success),
      duplicate/retry protection, usage logging.
    - Anonymous (deferred-auth funnel steps): server-side IP rate-limited
      (see ratelimit.py), runs free but still logs a usage job.

    Returns (result, meta) where meta = {credits, charged, counted_creation} or {}.
    """
    if not user:
        # Anonymous funnel step: enforce server-side rate limit FIRST (cost/abuse).
        if request is not None:
            try:
                await ratelimit.enforce_anon(request, task, proj["id"])
            except ratelimit.AnonRateLimited as e:
                status = 429
                raise HTTPException(status_code=status, detail={
                    "message": e.message, "code": f"anon_{e.reason}",
                    "retry_after": e.retry_after, "anon_limited": True,
                })
        # log usage, no charge.
        routing = model_router.route(task)
        rec = {
            "id": f"job_{uuid.uuid4().hex[:12]}", "user_id": None, "project_id": proj["id"],
            "task": task, "tier": routing["tier"], "provider": routing["provider"],
            "model": routing["model"], "estimated_credits": 0, "credits_charged": 0,
            "status": "running", "retry_count": 0, "error": None,
            "started_at": now_iso(), "completed_at": None, "created_at": now_iso(),
        }
        await db.generation_jobs.insert_one(dict(rec))
        try:
            result = await coro_factory()
        except HTTPException:
            await jobs.fail(rec, "http_error"); raise
        except Exception as e:
            await jobs.fail(rec, str(e))
            raise HTTPException(status_code=502, detail={
                "message": f"Generation failed: {e}", "code": "generation_failed",
                "refunded": 0, "balance": None,
            })
        await db.generation_jobs.update_one({"id": rec["id"]}, {"$set": {"status": "completed", "completed_at": now_iso()}})
        return result, {}

    try:
        job = await jobs.begin(user, proj, task)
    except (jobs.FeatureLocked, jobs.InsufficientCredits, jobs.CreationLimitReached,
            jobs.DuplicateJob, jobs.RetryLimitReached) as e:
        _job_http(e)

    try:
        result = await coro_factory()
    except HTTPException:
        await jobs.fail(job, "http_error"); raise
    except Exception as e:
        # Credits are charged on success only, so a pre-completion failure has not
        # charged anything (refunded=0). If a charge had occurred, jobs.fail refunds it.
        refunded = await jobs.fail(job, str(e))
        try:
            balance = await billing.get_balance(user["user_id"])
        except Exception:
            balance = None
        raise HTTPException(status_code=502, detail={
            "message": f"Generation failed: {e}", "code": "generation_failed",
            "refunded": refunded, "balance": balance,
        })

    try:
        info = await jobs.complete(user, proj, job)
    except jobs.InsufficientCredits as e:
        _job_http(e)
    if info.get("counted_creation"):
        proj["counted_as_creation"] = True
        await db.projects.update_one({"id": proj["id"]}, {"$set": {"counted_as_creation": True}})
    return result, {"credits": info["balance"], "charged": info["cost"], "counted_creation": info.get("counted_creation", False)}


def _with_economy(proj_out: dict, meta: dict) -> dict:
    """Attach lightweight (non-persisted) economy feedback to a serialized project."""
    if meta:
        proj_out = dict(proj_out)
        proj_out["_economy"] = {"credits": meta.get("credits"), "charged": meta.get("charged", 0)}
    return proj_out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def load_project(project_id: str) -> dict:
    proj = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


def check_access(proj: dict, user: Optional[dict]):
    """Anonymous projects (user_id None) are open. Owned projects require the owner."""
    owner = proj.get("user_id")
    if owner:
        if not user or user.get("user_id") != owner:
            raise HTTPException(status_code=403, detail="Not authorized for this project")


async def save_project(project_id: str, updates: dict):
    updates["updated_at"] = now_iso()
    await db.projects.update_one({"id": project_id}, {"$set": updates})


async def claim_if_needed(proj: dict, user: dict):
    if not proj.get("user_id"):
        await db.projects.update_one({"id": proj["id"]}, {"$set": {"user_id": user["user_id"]}})
        proj["user_id"] = user["user_id"]


def _register_asset(proj: dict, kind: str, filename: str, data: bytes, mime: str, key: str = None) -> dict:
    pdir = GENERATED_DIR / proj["id"]
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / filename
    path.write_bytes(data)
    asset = {
        "id": f"asset_{uuid.uuid4().hex[:10]}",
        "type": kind,
        "key": key,
        "filename": filename,
        "mime": mime,
        "path": str(path),
        "size": len(data),
        "created_at": now_iso(),
    }
    assets = proj.get("assets", []) or []
    # replace any asset of same type+key
    assets = [a for a in assets if not (a.get("type") == kind and a.get("key") == key)]
    assets.append(asset)
    proj["assets"] = assets
    return asset


def _asset_bytes(proj: dict, asset_id: str):
    for a in proj.get("assets", []) or []:
        if a["id"] == asset_id:
            p = Path(a["path"])
            if p.exists():
                return p.read_bytes(), a.get("mime", "application/octet-stream")
    return None, None


def _find_asset(proj: dict, kind: str, key=None):
    for a in proj.get("assets", []) or []:
        if a.get("type") == kind and a.get("key") == key:
            return a
    return None


# ---------------------------------------------------------------------------
# Config / Settings
# ---------------------------------------------------------------------------
AVAILABLE_MODELS = {
    "openai": ["gpt-5.4", "gpt-5.4-mini", "gpt-5.2", "gpt-4.1", "gpt-4.1-mini"],
    "anthropic": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-6"],
    "gemini": ["gemini-3.1-pro-preview", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-flash-preview"],
}
AGENT_CATEGORIES = ["research", "opportunities", "strategy", "writing", "qa"]


@api.get("/")
async def root():
    return {"app": "Khova AI", "status": "ok"}


@api.get("/config/models")
async def config_models(user: dict = Depends(get_admin_user)):
    """Admin/developer-only: internal model routing visibility. Never exposed to normal users."""
    return {
        "providers": AVAILABLE_MODELS,
        "categories": AGENT_CATEGORIES,
        "defaults": {k: DEFAULT_MODELS[k] for k in AGENT_CATEGORIES},
        "tiers": model_router.TIER_CATEGORY,
        "task_tiers": model_router.TASK_TIER,
        "task_costs": billing.TASK_COSTS,
        "note": "Internal routing. Research uses Gemini web-search grounding for real citations.",
    }


class SettingsBody(BaseModel):
    ui_language: Optional[str] = None
    product_language: Optional[str] = None
    models_config: Optional[Dict[str, Any]] = None


@api.get("/settings")
async def get_settings(user: Optional[dict] = Depends(get_optional_user)):
    defaults = {"ui_language": "id", "product_language": "id", "models_config": {}}
    if user and user.get("settings"):
        defaults.update(user["settings"])
    return defaults


@api.put("/settings")
async def put_settings(body: SettingsBody, user: Optional[dict] = Depends(get_optional_user)):
    # NOTE: models_config is intentionally ignored — model/provider selection is
    # internal to Khova and never user-controlled.
    settings = {k: v for k, v in body.model_dump().items() if v is not None and k != "models_config"}
    if user:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"settings": settings}})
    return settings


# ---------------------------------------------------------------------------
# Economy — plan / credits / redeem (server-side authoritative)
# ---------------------------------------------------------------------------
@api.get("/me/economy")
async def my_economy(user: dict = Depends(get_current_user)):
    user = await billing.ensure_user_economy(user)
    return billing.economy_view(user)


@api.get("/me/usage")
async def my_usage(user: dict = Depends(get_current_user)):
    """The authenticated user's OWN usage insights (deterministic, no AI).

    Scoped strictly to this user_id — a user can never see another user's data.
    Aggregates the existing server-side generation-job records."""
    user = await billing.ensure_user_economy(user)
    uid = user["user_id"]

    per_project = {}       # project_id -> {credits_used, generations}
    total_used = 0
    total_generations = 0
    total_refunded = 0
    async for j in db.generation_jobs.find(
        {"user_id": uid, "status": "completed"},
        {"_id": 0, "project_id": 1, "credits_charged": 1, "task": 1},
    ):
        charged = int(j.get("credits_charged") or 0)
        pid = j.get("project_id") or "unknown"
        slot = per_project.setdefault(pid, {"credits_used": 0, "generations": 0})
        slot["credits_used"] += charged
        slot["generations"] += 1
        total_used += charged
        total_generations += 1
    async for j in db.generation_jobs.find(
        {"user_id": uid, "credits_refunded": {"$gt": 0}}, {"_id": 0, "credits_refunded": 1},
    ):
        total_refunded += int(j.get("credits_refunded") or 0)

    # Attach titles (only this user's projects).
    titles = {}
    async for p in db.projects.find({"user_id": uid}, {"_id": 0, "id": 1, "title": 1, "format": 1}):
        titles[p["id"]] = {"title": p.get("title") or "Untitled", "format": p.get("format")}

    products = []
    for pid, agg in per_project.items():
        meta = titles.get(pid, {})
        products.append({
            "project_id": pid,
            "title": meta.get("title", "Untitled"),
            "format": meta.get("format"),
            "credits_used": agg["credits_used"],
            "generations": agg["generations"],
        })
    products.sort(key=lambda x: (-x["credits_used"], x["title"].lower()))

    eco = billing.economy_view(user)
    return {
        "credits_remaining": eco["credits"],
        "plan": eco["plan"],
        "total_credits_used": total_used,
        "total_credits_refunded": total_refunded,
        "total_generations": total_generations,
        "product_generations": len(products),
        "products": products,
    }


class RedeemBody(BaseModel):
    code: str


@api.post("/redeem")
async def redeem(body: RedeemBody, user: dict = Depends(get_current_user)):
    try:
        result = await billing.redeem_code(user, body.code)
    except ValueError as e:
        reason = str(e)
        raise HTTPException(status_code=400, detail=billing.REDEEM_MESSAGES.get(reason, "This code could not be redeemed."))
    msg_parts = []
    if result.get("plan_granted"):
        msg_parts.append(f"Plan upgraded to {result['plan_granted'].title()}")
    if result.get("credits_granted"):
        msg_parts.append(f"+{result['credits_granted']} credits")
    result["message"] = " · ".join(msg_parts) or "Code redeemed successfully."
    return result


# ---------------------------------------------------------------------------
# Admin / developer
# ---------------------------------------------------------------------------
@api.get("/admin/overview")
async def admin_overview(user: dict = Depends(get_admin_user)):
    users = await db.users.count_documents({})
    jobs_count = await db.generation_jobs.count_documents({})
    active_codes = await db.redeem_codes.count_documents({"active": True})
    consumed = 0
    async for l in db.credit_ledger.find({"delta": {"$lt": 0}}, {"delta": 1}):
        consumed += abs(int(l.get("delta", 0)))
    return {"users": users, "jobs": jobs_count, "active_codes": active_codes, "credits_consumed": consumed}


@api.get("/admin/users")
async def admin_users(user: dict = Depends(get_admin_user)):
    docs = await db.users.find({}, {"_id": 0, "user_id": 1, "email": 1, "name": 1, "role": 1,
                                    "plan": 1, "credits": 1, "creations_used": 1, "created_at": 1}).sort("created_at", -1).to_list(500)
    for d in docs:
        d.setdefault("plan", "free"); d.setdefault("credits", 0); d.setdefault("creations_used", 0); d.setdefault("role", "user")
    return docs


class AdminUserPatch(BaseModel):
    plan: Optional[str] = None
    credits_delta: Optional[int] = None
    role: Optional[str] = None


@api.patch("/admin/users/{target_user_id}")
async def admin_update_user(target_user_id: str, body: AdminUserPatch, user: dict = Depends(get_admin_user)):
    updates = {}
    if body.plan:
        if body.plan not in billing.PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan")
        updates["plan"] = body.plan
    if body.role in ("user", "admin"):
        updates["role"] = body.role
    if updates:
        await db.users.update_one({"user_id": target_user_id}, {"$set": updates})
    if body.credits_delta:
        if body.credits_delta > 0:
            await billing.grant_credits(target_user_id, body.credits_delta, f"admin_grant:{user['user_id']}")
        else:
            await billing.deduct_credits(target_user_id, abs(body.credits_delta), f"admin_adjust:{user['user_id']}")
    doc = await db.users.find_one({"user_id": target_user_id}, {"_id": 0})
    return serialize_doc(doc)


@api.get("/admin/jobs")
async def admin_jobs(user: dict = Depends(get_admin_user)):
    docs = await db.generation_jobs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api.get("/admin/codes")
async def admin_codes(user: dict = Depends(get_admin_user)):
    docs = await db.redeem_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


class CreateCodeBody(BaseModel):
    plan: Optional[str] = None
    credits: int = 0
    max_redemptions: int = 1
    expires_days: Optional[int] = None
    prefix: str = "KHOVA"


@api.post("/admin/codes")
async def admin_create_code(body: CreateCodeBody, user: dict = Depends(get_admin_user)):
    try:
        doc = await billing.create_redeem_code(user, plan=body.plan, credits=body.credits,
                                               max_redemptions=body.max_redemptions,
                                               expires_days=body.expires_days, prefix=body.prefix)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan for code")
    return doc


# ---------------------------------------------------------------------------
# Projects CRUD
# ---------------------------------------------------------------------------
class CreateProject(BaseModel):
    title: Optional[str] = None
    ui_language: str = "id"
    product_language: str = "id"
    models_config: Optional[Dict[str, Any]] = None


def _new_project_doc(body: CreateProject, user: Optional[dict]) -> dict:
    return {
        "id": f"prj_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"] if user else None,
        "title": body.title or "Produk Baru",
        "status": "draft",
        "current_step": "discover",
        "ui_language": body.ui_language or "id",
        "product_language": body.product_language or "id",
        "models_config": body.models_config or {},
        "discover": {},
        "research": None,
        "opportunities": [],
        "selected_opportunity_id": None,
        "positioning": None,
        "transformation": None,
        "format": None,
        "ebook": None,
        "spreadsheet": None,
        "website": None,
        "qa": [],
        "branding": None,
        "assets": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


@api.post("/projects")
async def create_project(body: CreateProject, user: Optional[dict] = Depends(get_optional_user)):
    doc = _new_project_doc(body, user)
    await db.projects.insert_one(dict(doc))
    return serialize_doc(doc)


@api.get("/projects")
async def list_projects(user: dict = Depends(get_current_user)):
    docs = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).sort("updated_at", -1).to_list(200)
    # lightweight list
    out = []
    for d in docs:
        out.append({
            "id": d["id"], "title": d.get("title"), "status": d.get("status"),
            "current_step": d.get("current_step"), "format": d.get("format"),
            "product_language": d.get("product_language"),
            "created_at": d.get("created_at"), "updated_at": d.get("updated_at"),
            "opportunity_count": len(d.get("opportunities", []) or []),
        })
    return out


@api.get("/projects/{project_id}")
async def get_project(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    return serialize_doc(proj)


class PatchProject(BaseModel):
    title: Optional[str] = None
    ui_language: Optional[str] = None
    product_language: Optional[str] = None
    models_config: Optional[Dict[str, Any]] = None
    positioning: Optional[Dict[str, Any]] = None
    transformation: Optional[Dict[str, Any]] = None


@api.patch("/projects/{project_id}")
async def patch_project(project_id: str, body: PatchProject, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await save_project(project_id, updates)
    proj.update(updates)
    return serialize_doc(proj)


@api.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await db.projects.delete_one({"id": project_id})
    return {"ok": True}


@api.post("/projects/{project_id}/duplicate")
async def duplicate_project(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    new = dict(proj)
    new.pop("_id", None)
    new["id"] = f"prj_{uuid.uuid4().hex[:12]}"
    new["user_id"] = user["user_id"]
    new["title"] = (proj.get("title") or "Produk") + " (Salinan)"
    new["assets"] = []  # don't copy files
    new["created_at"] = now_iso()
    new["updated_at"] = now_iso()
    await db.projects.insert_one(dict(new))
    return serialize_doc(new)


# ---------------------------------------------------------------------------
# Pipeline — anonymous allowed (Discover -> Format)
# ---------------------------------------------------------------------------
class DiscoverBody(BaseModel):
    mode: str = "know"  # "know" | "explore"
    idea: Optional[str] = ""
    expertise: Optional[str] = ""
    experience: Optional[str] = ""
    audience: Optional[str] = ""
    interests: Optional[str] = ""
    skills: Optional[str] = ""
    story: Optional[str] = ""
    problem: Optional[str] = ""
    framework: Optional[str] = ""
    industry: Optional[str] = ""
    preferred_audience: Optional[str] = ""
    uploads: Optional[List[Dict[str, Any]]] = None


@api.post("/projects/{project_id}/discover")
async def save_discover(project_id: str, body: DiscoverBody, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    discover = body.model_dump()
    title = proj.get("title")
    if body.idea and (not title or title in ("Produk Baru",)):
        title = body.idea[:60]
    await save_project(project_id, {"discover": discover, "current_step": "research", "title": title})
    proj["discover"] = discover
    proj["current_step"] = "research"
    proj["title"] = title
    return serialize_doc(proj)


@api.post("/projects/{project_id}/research")
async def run_research(project_id: str, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    async def _do():
        b = await agents.run_market_research(proj.get("discover", {}), proj.get("product_language", "id"), {})
        b["generated_at"] = now_iso()
        return b
    bundle, meta = await run_ai(user, proj, "research", _do, request=request)
    await save_project(project_id, {"research": bundle, "current_step": "opportunities"})
    proj["research"] = bundle
    proj["current_step"] = "opportunities"
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/opportunities")
async def gen_opportunities(project_id: str, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    if not proj.get("research"):
        raise HTTPException(status_code=400, detail="Run market research first")
    async def _do():
        return await agents.generate_opportunities(proj.get("discover", {}), proj["research"], proj.get("product_language", "id"), {})
    opps, meta = await run_ai(user, proj, "opportunities", _do, request=request)
    await save_project(project_id, {"opportunities": opps, "current_step": "opportunities"})
    proj["opportunities"] = opps
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/opportunities/save/{opportunity_id}")
async def toggle_save_opportunity(project_id: str, opportunity_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opps = proj.get("opportunities", [])
    for o in opps:
        if o["id"] == opportunity_id:
            o["saved"] = not o.get("saved", False)
    await save_project(project_id, {"opportunities": opps})
    return serialize_doc(proj)


class SelectOpp(BaseModel):
    opportunity_id: str


@api.post("/projects/{project_id}/select-opportunity")
async def select_opportunity(project_id: str, body: SelectOpp, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ids = [o["id"] for o in proj.get("opportunities", [])]
    if body.opportunity_id not in ids:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    await save_project(project_id, {"selected_opportunity_id": body.opportunity_id, "current_step": "positioning"})
    proj["selected_opportunity_id"] = body.opportunity_id
    proj["current_step"] = "positioning"
    return serialize_doc(proj)


def _selected_opp(proj):
    sid = proj.get("selected_opportunity_id")
    for o in proj.get("opportunities", []):
        if o["id"] == sid:
            return o
    return None


@api.post("/projects/{project_id}/positioning")
async def gen_positioning(project_id: str, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opp = _selected_opp(proj)
    if not opp:
        raise HTTPException(status_code=400, detail="Select an opportunity first")
    async def _do():
        return await agents.generate_positioning(opp, proj.get("discover", {}), proj.get("product_language", "id"), {})
    pos, meta = await run_ai(user, proj, "positioning", _do, request=request)
    await save_project(project_id, {"positioning": pos, "current_step": "transformation"})
    proj["positioning"] = pos
    proj["current_step"] = "transformation"
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/transformation")
async def gen_transformation(project_id: str, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opp = _selected_opp(proj)
    if not opp or not proj.get("positioning"):
        raise HTTPException(status_code=400, detail="Positioning required first")
    async def _do():
        return await agents.generate_transformation(opp, proj["positioning"], proj.get("product_language", "id"), {})
    tr, meta = await run_ai(user, proj, "transformation", _do, request=request)
    # keep existing palette if set
    existing_palette = (proj.get("transformation") or {}).get("palette") if proj.get("transformation") else None
    tr["palette"] = existing_palette or {
        "primary": "#0B6E6B", "secondary": "#111C2E", "accent": "#C07A2B",
        "background": "#FBFAF7", "text": "#0B1220",
    }
    await save_project(project_id, {"transformation": tr, "current_step": "format"})
    proj["transformation"] = tr
    proj["current_step"] = "format"
    return _with_economy(serialize_doc(proj), meta)


class PaletteBody(BaseModel):
    palette: Dict[str, str]


@api.patch("/projects/{project_id}/palette")
async def set_palette(project_id: str, body: PaletteBody, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    tr = proj.get("transformation") or {}
    tr["palette"] = body.palette
    await save_project(project_id, {"transformation": tr})
    proj["transformation"] = tr
    return serialize_doc(proj)


class FormatBody(BaseModel):
    format: str  # ebook | spreadsheet | website


@api.post("/projects/{project_id}/format")
async def set_format(project_id: str, body: FormatBody, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    if body.format not in ("ebook", "spreadsheet", "website"):
        raise HTTPException(status_code=400, detail="Format not supported in V1")
    await save_project(project_id, {"format": body.format, "current_step": "create"})
    proj["format"] = body.format
    proj["current_step"] = "create"
    return serialize_doc(proj)


# ---------------------------------------------------------------------------
# GENERATION — requires auth (deferred login)
# ---------------------------------------------------------------------------
def _require_pipeline(proj):
    opp = _selected_opp(proj)
    if not opp or not proj.get("positioning") or not proj.get("transformation"):
        raise HTTPException(status_code=400, detail="Complete positioning and transformation first")
    return opp


# ----- EBOOK -----
@api.post("/projects/{project_id}/ebook/plan")
async def ebook_plan(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    async def _do():
        return await agents.generate_ebook_plan(opp, proj["positioning"], proj["transformation"], proj.get("product_language", "id"), {})
    plan, meta = await run_ai(user, proj, "ebook_plan", _do)
    palette = (proj.get("transformation") or {}).get("palette", {})
    toc = plan.get("toc", []) or []
    # Enforce plan chapter limit (free-tier gets a smaller product)
    max_ch = billing.plan_limit(user, "max_chapters")
    if isinstance(max_ch, int) and len(toc) > max_ch:
        toc = toc[:max_ch]
    ebook = {
        "meta": plan.get("meta", {}),
        "toc": toc,
        "visuals": plan.get("visuals", []),
        "bonuses": plan.get("bonuses", []),
        "sections": [],
        "introduction_html": "",
        "design_system": {
            "colors": palette,
            "typography": "serif",
            "visual_style": "premium editorial",
        },
        "cover_asset_id": None,
        "illustrations": {},
        "progress": {"done": 0, "total": len(toc)},
    }
    await save_project(project_id, {"ebook": ebook, "format": "ebook", "user_id": user["user_id"], "status": "creating"})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


class SectionBody(BaseModel):
    chapter_num: int
    tone: Optional[str] = "professional and clear"


@api.post("/projects/{project_id}/ebook/section")
async def ebook_section(project_id: str, body: SectionBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook:
        raise HTTPException(status_code=400, detail="Generate the ebook plan first")
    chapter = next((c for c in ebook.get("toc", []) if c.get("chapter_num") == body.chapter_num), None)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    async def _do():
        return await agents.generate_ebook_section(chapter, ebook.get("meta", {}), proj.get("transformation"), proj.get("product_language", "id"), {}, body.tone or "professional and clear")
    html, meta = await run_ai(user, proj, "ebook_section", _do)
    sections = [s for s in ebook.get("sections", []) if s.get("chapter_num") != body.chapter_num]
    sections.append({"chapter_num": body.chapter_num, "title": chapter.get("title"), "content_html": html, "status": "done"})
    sections.sort(key=lambda s: s.get("chapter_num", 0))
    ebook["sections"] = sections
    ebook["progress"] = {"done": len(sections), "total": len(ebook.get("toc", []))}
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/ebook/intro")
async def ebook_intro(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook:
        raise HTTPException(status_code=400, detail="Generate the ebook plan first")
    async def _do():
        return await agents.generate_introduction(ebook.get("meta", {}), proj.get("transformation"), proj.get("product_language", "id"), {})
    html, meta = await run_ai(user, proj, "ebook_intro", _do)
    ebook["introduction_html"] = html
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


class RewriteBody(BaseModel):
    chapter_num: int
    instruction: str  # e.g. "expand", "shorten", "more casual tone"


@api.post("/projects/{project_id}/ebook/section/rewrite")
async def ebook_section_rewrite(project_id: str, body: RewriteBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    sec = next((s for s in (ebook.get("sections", []) if ebook else []) if s.get("chapter_num") == body.chapter_num), None)
    if not sec:
        raise HTTPException(status_code=404, detail="Section not generated yet")
    is_math = bool((ebook.get("meta") or {}).get("is_math_heavy"))
    async def _do():
        return await agents.rewrite_section(sec["content_html"], body.instruction, proj.get("product_language", "id"), {}, is_math)
    new_html, meta = await run_ai(user, proj, "ebook_rewrite", _do)
    sec["content_html"] = new_html
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


class DesignBody(BaseModel):
    design_system: Dict[str, Any]


@api.patch("/projects/{project_id}/ebook/design")
async def ebook_design(project_id: str, body: DesignBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook") or {}
    ebook["design_system"] = {**ebook.get("design_system", {}), **body.design_system}
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return serialize_doc(proj)


@api.post("/projects/{project_id}/ebook/cover")
async def ebook_cover(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook") or {}
    palette = (proj.get("transformation") or {}).get("palette", {})
    prompt = build_cover_prompt(proj.get("branding"), ebook.get("meta", {}), palette)
    async def _do():
        data, mime = await generate_image(prompt, {})
        if not data:
            raise HTTPException(status_code=502, detail="Image generation failed. Please retry.")
        return (data, mime)
    (data, mime), meta = await run_ai(user, proj, "cover", _do)
    ext = "jpg" if "jpeg" in (mime or "") else "png"
    asset = _register_asset(proj, "cover", f"cover.{ext}", data, mime, key="cover")
    ebook["cover_asset_id"] = asset["id"]
    await save_project(project_id, {"ebook": ebook, "assets": proj["assets"]})
    return _with_economy(serialize_doc(proj), meta)


class IllustrationBody(BaseModel):
    chapter_num: int
    prompt: Optional[str] = None


@api.post("/projects/{project_id}/ebook/illustration")
async def ebook_illustration(project_id: str, body: IllustrationBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook") or {}
    prompt = body.prompt
    if not prompt:
        v = next((x for x in ebook.get("visuals", []) if x.get("chapter_num") == body.chapter_num), None)
        prompt = (v or {}).get("prompt") or f"A clean editorial illustration for chapter {body.chapter_num}"
    palette = (proj.get("transformation") or {}).get("palette", {})
    colors = ", ".join([v for v in palette.values() if v])
    full_prompt = f"{prompt}. Use color palette: {colors}. Clean, modern, no text, no words."
    async def _do():
        data, mime = await generate_image(full_prompt, {})
        if not data:
            raise HTTPException(status_code=502, detail="Image generation failed. Please retry.")
        return (data, mime)
    (data, mime), meta = await run_ai(user, proj, "illustration", _do)
    ext = "jpg" if "jpeg" in (mime or "") else "png"
    asset = _register_asset(proj, "illustration", f"illo_{body.chapter_num}.{ext}", data, mime, key=f"ch{body.chapter_num}")
    illos = ebook.get("illustrations", {}) or {}
    illos[str(body.chapter_num)] = asset["id"]
    ebook["illustrations"] = illos
    await save_project(project_id, {"ebook": ebook, "assets": proj["assets"]})
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/ebook/export")
async def ebook_export(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook or not ebook.get("sections"):
        raise HTTPException(status_code=400, detail="Generate ebook chapters first")
    # cover
    cover_bytes, cover_mime = (None, "image/png")
    if ebook.get("cover_asset_id"):
        cover_bytes, cover_mime = _asset_bytes(proj, ebook["cover_asset_id"])
    # illustrations
    illustrations = {}
    for ch, aid in (ebook.get("illustrations", {}) or {}).items():
        b, m = _asset_bytes(proj, aid)
        if b:
            illustrations[int(ch)] = (b, m)
    html = exporters.build_ebook_html(ebook, proj.get("branding"), proj.get("transformation"), cover_bytes, cover_mime or "image/png", illustrations, proj.get("product_language", "id"))
    pdf = exporters.html_to_pdf(html)
    title = (ebook.get("meta", {}) or {}).get("title", "ebook")
    safe = "".join([c if c.isalnum() else "_" for c in title])[:40] or "ebook"
    asset = _register_asset(proj, "pdf", f"{safe}.pdf", pdf, "application/pdf", key="ebook_pdf")
    await save_project(project_id, {"assets": proj["assets"], "status": "complete", "current_step": "export"})
    return {"project": serialize_doc(proj), "asset": asset}


@api.get("/projects/{project_id}/ebook/preview-html")
async def ebook_preview_html(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook:
        raise HTTPException(status_code=400, detail="No ebook yet")
    cover_bytes, cover_mime = (None, "image/png")
    if ebook.get("cover_asset_id"):
        cover_bytes, cover_mime = _asset_bytes(proj, ebook["cover_asset_id"])
    illustrations = {}
    for ch, aid in (ebook.get("illustrations", {}) or {}).items():
        b, m = _asset_bytes(proj, aid)
        if b:
            illustrations[int(ch)] = (b, m)
    html = exporters.build_ebook_html(ebook, proj.get("branding"), proj.get("transformation"), cover_bytes, cover_mime or "image/png", illustrations, proj.get("product_language", "id"))
    return HTMLResponse(content=html)


@api.get("/projects/{project_id}/ebook/design-check")
async def ebook_design_check(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook") or {}
    return exporters.design_consistency_check(ebook.get("design_system", {}), proj.get("transformation"))


# ----- SPREADSHEET -----
@api.post("/projects/{project_id}/spreadsheet/spec")
async def spreadsheet_spec(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    async def _do():
        return await agents.generate_spreadsheet_spec(opp, proj["positioning"], proj["transformation"], proj.get("product_language", "id"), {})
    spec, meta = await run_ai(user, proj, "spreadsheet_spec", _do)
    ss = {"concept": spec.get("concept"), "product_type": spec.get("product_type"), "sheets": spec.get("sheets", []), "asset_id": None}
    await save_project(project_id, {"spreadsheet": ss, "format": "spreadsheet", "status": "creating"})
    proj["spreadsheet"] = ss
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/spreadsheet/build")
async def spreadsheet_build(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ss = proj.get("spreadsheet")
    if not ss or not ss.get("sheets"):
        raise HTTPException(status_code=400, detail="Generate the spreadsheet spec first")
    palette = (proj.get("transformation") or {}).get("palette", {})
    try:
        data = exporters.build_xlsx(ss, palette)
    except Exception as e:
        logger.error(f"xlsx build failed: {e}")
        raise HTTPException(status_code=500, detail=f"Spreadsheet build failed: {e}")
    concept = ss.get("product_type") or ss.get("concept") or "spreadsheet"
    safe = "".join([c if c.isalnum() else "_" for c in str(concept)])[:40] or "spreadsheet"
    asset = _register_asset(proj, "xlsx", f"{safe}.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="xlsx")
    ss["asset_id"] = asset["id"]
    await save_project(project_id, {"spreadsheet": ss, "assets": proj["assets"], "status": "complete", "current_step": "export"})
    return {"project": serialize_doc(proj), "asset": asset}


# ----- WEBSITE (DRAFT / PREVIEW / PUBLISHED state machine) -----
class WebsiteStyleBody(BaseModel):
    style: str = "Modern"


def _web_defaults(web: dict) -> dict:
    """Ensure a website dict has all state fields."""
    web = web or {}
    web.setdefault("status", "draft")     # draft | published
    web.setdefault("spec", None)          # editable DRAFT spec
    web.setdefault("style", "Modern")
    web.setdefault("draft_html", None)    # last PREVIEW build of the draft
    web.setdefault("published", None)     # PUBLISHED snapshot {spec, html, style, published_at}
    web.setdefault("slug", None)
    web.setdefault("asset_id", None)
    return web


@api.post("/projects/{project_id}/website/spec")
async def website_spec(project_id: str, body: WebsiteStyleBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    async def _do():
        return await agents.generate_website_spec(opp, proj["positioning"], proj["transformation"], body.style, proj.get("product_language", "id"), {})
    spec, meta = await run_ai(user, proj, "website_spec", _do)
    web = _web_defaults(proj.get("website"))
    web["style"] = body.style
    web["spec"] = spec           # new DRAFT (does NOT touch published snapshot)
    web["status"] = "draft"
    web["draft_html"] = exporters.build_website_html(spec, (proj.get("transformation") or {}).get("palette", {}), body.style, proj.get("product_language", "id"))
    await save_project(project_id, {"website": web, "format": "website", "status": "creating"})
    proj["website"] = web
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/website/build")
async def website_build(project_id: str, user: dict = Depends(get_current_user)):
    """Deterministic PREVIEW build of the DRAFT (no AI, no credits)."""
    proj = await load_project(project_id)
    check_access(proj, user)
    web = _web_defaults(proj.get("website"))
    if not web.get("spec"):
        raise HTTPException(status_code=400, detail="Generate the website spec first")
    palette = (proj.get("transformation") or {}).get("palette", {})
    html = exporters.build_website_html(web["spec"], palette, web.get("style", "Modern"), proj.get("product_language", "id"))
    web["draft_html"] = html
    asset = _register_asset(proj, "html", "website.html", html.encode("utf-8"), "text/html", key="website")
    web["asset_id"] = asset["id"]
    await save_project(project_id, {"website": web, "assets": proj["assets"], "current_step": "export"})
    return {"project": serialize_doc(proj), "asset": asset, "url": f"/api/sites/{project_id}?preview=1"}


class WebsiteEditBody(BaseModel):
    spec: Dict[str, Any]


@api.patch("/projects/{project_id}/website/spec")
async def website_edit(project_id: str, body: WebsiteEditBody, user: dict = Depends(get_current_user)):
    """Edit + save the DRAFT spec (deterministic, no AI). Rebuilds draft preview."""
    proj = await load_project(project_id)
    check_access(proj, user)
    web = _web_defaults(proj.get("website"))
    web["spec"] = body.spec
    palette = (proj.get("transformation") or {}).get("palette", {})
    web["draft_html"] = exporters.build_website_html(body.spec, palette, web.get("style", "Modern"), proj.get("product_language", "id"))
    await save_project(project_id, {"website": web})
    proj["website"] = web
    return serialize_doc(proj)


class WebsiteSectionBody(BaseModel):
    section: str                 # e.g. "hero", "problem", "benefits", "faq", "final_cta"
    instruction: Optional[str] = None


@api.post("/projects/{project_id}/website/section/regenerate")
async def website_section_regenerate(project_id: str, body: WebsiteSectionBody, user: dict = Depends(get_current_user)):
    """Regenerate a SINGLE website section (section-level, cheaper than full regen)."""
    proj = await load_project(project_id)
    check_access(proj, user)
    web = _web_defaults(proj.get("website"))
    if not web.get("spec"):
        raise HTTPException(status_code=400, detail="Generate the website spec first")
    if body.section not in (web["spec"] or {}):
        raise HTTPException(status_code=404, detail="Unknown website section")
    async def _do():
        return await agents.regenerate_website_section(web["spec"], body.section, body.instruction, proj.get("product_language", "id"), {})
    new_section, meta = await run_ai(user, proj, "website_section", _do)
    web["spec"][body.section] = new_section
    palette = (proj.get("transformation") or {}).get("palette", {})
    web["draft_html"] = exporters.build_website_html(web["spec"], palette, web.get("style", "Modern"), proj.get("product_language", "id"))
    web["status"] = "draft"
    await save_project(project_id, {"website": web})
    proj["website"] = web
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/website/publish")
async def website_publish(project_id: str, user: dict = Depends(get_current_user)):
    """Publish the current DRAFT to a stable public URL. Feature-gated (creator+).
    The editable draft is preserved; publishing snapshots the draft."""
    proj = await load_project(project_id)
    check_access(proj, user)
    if not billing.feature_enabled(user, "website_publish"):
        raise HTTPException(status_code=403, detail="Publishing websites requires the Creator plan or higher. Redeem a code or upgrade.")
    web = _web_defaults(proj.get("website"))
    if not web.get("spec"):
        raise HTTPException(status_code=400, detail="Generate the website spec first")
    palette = (proj.get("transformation") or {}).get("palette", {})
    html = exporters.build_website_html(web["spec"], palette, web.get("style", "Modern"), proj.get("product_language", "id"))
    slug = web.get("slug") or project_id
    import copy
    web["slug"] = slug
    web["status"] = "published"
    web["published"] = {
        "spec": copy.deepcopy(web["spec"]),   # snapshot — draft can keep changing
        "html": html,
        "style": web.get("style", "Modern"),
        "slug": slug,
        "published_at": now_iso(),
    }
    await save_project(project_id, {"website": web, "status": "complete", "current_step": "export"})
    proj["website"] = web
    out = serialize_doc(proj)
    out["public_url"] = f"/api/sites/{slug}"
    return out


@api.post("/projects/{project_id}/website/unpublish")
async def website_unpublish(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    web = _web_defaults(proj.get("website"))
    web["status"] = "draft"
    if web.get("published"):
        web["published"]["unpublished_at"] = now_iso()
        web["published"]["live"] = False
    await save_project(project_id, {"website": web})
    proj["website"] = web
    return serialize_doc(proj)


class WebsiteStyleChangeBody(BaseModel):
    style: str


@api.patch("/projects/{project_id}/website/style")
async def website_set_style(project_id: str, body: WebsiteStyleChangeBody, user: dict = Depends(get_current_user)):
    """Apply a website visual THEME/preset deterministically (NO AI, NO credits).

    Only changes typography/spacing/radius/button treatment via the preset. The
    canonical product palette remains the source of truth for colors and is NOT
    replaced. Rebuilds the draft preview; the published snapshot is untouched
    until the user re-publishes."""
    proj = await load_project(project_id)
    check_access(proj, user)
    style = (body.style or "Modern")
    if style not in exporters.STYLE_PRESETS:
        raise HTTPException(status_code=400, detail="Unknown website theme")
    web = _web_defaults(proj.get("website"))
    if not web.get("spec"):
        raise HTTPException(status_code=400, detail="Generate the website spec first")
    web["style"] = style
    palette = (proj.get("transformation") or {}).get("palette", {})
    web["draft_html"] = exporters.build_website_html(web["spec"], palette, style, proj.get("product_language", "id"))
    await save_project(project_id, {"website": web})
    proj["website"] = web
    return serialize_doc(proj)


# ----- QA -----
class QABody(BaseModel):
    format: Optional[str] = None


def _content_text_for_qa(proj):
    fmt = proj.get("format")
    if fmt == "ebook" and proj.get("ebook"):
        parts = [proj["ebook"].get("introduction_html", "")]
        for s in proj["ebook"].get("sections", []):
            parts.append(f"# {s.get('title')}\n{s.get('content_html','')}")
        return fmt, "\n\n".join(parts)
    if fmt == "spreadsheet" and proj.get("spreadsheet"):
        import json as _j
        return fmt, _j.dumps(proj["spreadsheet"], ensure_ascii=False)
    if fmt == "website" and proj.get("website"):
        import json as _j
        return fmt, _j.dumps(proj["website"].get("spec", {}), ensure_ascii=False)
    return fmt, ""


@api.post("/projects/{project_id}/qa")
async def run_qa(project_id: str, body: QABody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    fmt, content = _content_text_for_qa(proj)
    if not content:
        raise HTTPException(status_code=400, detail="No product content to review yet")
    async def _do():
        return await agents.qa_review(fmt, content, proj.get("transformation"), proj.get("product_language", "id"), {})
    report, meta = await run_ai(user, proj, "qa", _do)
    report["format"] = fmt
    report["created_at"] = now_iso()
    report["id"] = f"qa_{uuid.uuid4().hex[:8]}"
    # assign stable ids + resolved flag to each issue (for section-level Apply)
    for iss in report.get("issues", []) or []:
        iss["id"] = f"iss_{uuid.uuid4().hex[:8]}"
        iss["resolved"] = False
    qa = proj.get("qa", []) or []
    qa.insert(0, report)
    await save_project(project_id, {"qa": qa, "current_step": "qa"})
    proj["qa"] = qa
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/qa/apply")
async def apply_qa(project_id: str, user: dict = Depends(get_current_user)):
    """Apply recommended improvements to ebook chapters (creates new versions, keeps originals)."""
    proj = await load_project(project_id)
    check_access(proj, user)
    if proj.get("format") != "ebook" or not proj.get("ebook"):
        raise HTTPException(status_code=400, detail="Apply improvements currently supports ebooks")
    qa = proj.get("qa", [])
    if not qa:
        raise HTTPException(status_code=400, detail="Run QA first")
    latest = qa[0]
    improvements = "; ".join(latest.get("recommended_improvements", [])[:6]) or "improve clarity, remove AI-sounding phrasing, tighten logic"
    ebook = proj["ebook"]
    is_math = bool((ebook.get("meta") or {}).get("is_math_heavy"))
    async def _do():
        for sec in ebook.get("sections", []):
            original = sec["content_html"]
            new_html = await agents.rewrite_section(original, f"Apply these QA improvements: {improvements}", proj.get("product_language", "id"), {}, is_math)
            sec.setdefault("versions", []).append({"content_html": original, "saved_at": now_iso()})
            sec["content_html"] = new_html
        return True
    _, meta = await run_ai(user, proj, "qa_apply", _do)
    # mark all issues resolved on the latest report
    for iss in latest.get("issues", []) or []:
        iss["resolved"] = True
    await save_project(project_id, {"ebook": ebook, "qa": qa})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


@api.post("/projects/{project_id}/qa/apply-issue/{issue_id}")
async def apply_qa_issue(project_id: str, issue_id: str, user: dict = Depends(get_current_user)):
    """Apply ONE specific QA improvement to only the affected section.

    - Rewrites just the targeted chapter (or the introduction for chapter 0).
    - Persists the change and keeps the prior version in history.
    - Marks that single issue as resolved (others untouched).
    - Never regenerates the whole product; unrelated sections are not changed.
    """
    proj = await load_project(project_id)
    check_access(proj, user)
    if proj.get("format") != "ebook" or not proj.get("ebook"):
        raise HTTPException(status_code=400, detail="Apply improvements currently supports ebooks")
    qa = proj.get("qa", [])
    if not qa:
        raise HTTPException(status_code=400, detail="Run QA first")
    latest = qa[0]
    issue = next((i for i in latest.get("issues", []) or [] if i.get("id") == issue_id), None)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found in the latest QA report")

    ebook = proj["ebook"]
    is_math = bool((ebook.get("meta") or {}).get("is_math_heavy"))
    ch = issue.get("chapter_num")
    try:
        ch = int(ch)
    except (TypeError, ValueError):
        ch = 0
    instruction = (
        f"Fix ONLY this specific quality issue without rewriting the whole section: "
        f"[{issue.get('type')}] {issue.get('detail','')}. Recommended fix: {issue.get('fix','')}. "
        f"Preserve everything else in the section unchanged."
    )

    # Resolve the target block: chapter 0 = introduction, otherwise a chapter section.
    target_label = None
    if ch and ch != 0:
        sec = next((s for s in ebook.get("sections", []) if s.get("chapter_num") == ch), None)
        if not sec:
            # fall back to introduction if the chapter hasn't been generated
            ch = 0
        else:
            target_label = f"chapter {ch}"
    if not ch or ch == 0:
        if not ebook.get("introduction_html"):
            raise HTTPException(status_code=400, detail="Nothing to fix: the referenced section has not been generated yet")
        target_label = "introduction"

    async def _do():
        if target_label == "introduction":
            original = ebook.get("introduction_html", "")
            new_html = await agents.rewrite_section(original, instruction, proj.get("product_language", "id"), {}, is_math)
            return ("intro", original, new_html)
        original = sec["content_html"]
        new_html = await agents.rewrite_section(original, instruction, proj.get("product_language", "id"), {}, is_math)
        return ("chapter", original, new_html)

    (kind, original, new_html), meta = await run_ai(user, proj, "qa_apply", _do)
    if kind == "intro":
        ebook.setdefault("intro_versions", []).append({"content_html": original, "saved_at": now_iso()})
        ebook["introduction_html"] = new_html
    else:
        sec.setdefault("versions", []).append({"content_html": original, "saved_at": now_iso()})
        sec["content_html"] = new_html

    issue["resolved"] = True
    await save_project(project_id, {"ebook": ebook, "qa": qa})
    proj["ebook"] = ebook
    out = _with_economy(serialize_doc(proj), meta)
    out["_applied"] = {"issue_id": issue_id, "target": target_label}
    return out



# ----- BRANDING -----
class BrandingBody(BaseModel):
    style: str = "Premium"


@api.post("/projects/{project_id}/branding")
async def gen_branding(project_id: str, body: BrandingBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    async def _do():
        return await agents.generate_branding(opp, proj["positioning"], proj["transformation"], body.style, proj.get("product_language", "id"), {})
    brand, meta = await run_ai(user, proj, "branding", _do)
    brand["style"] = body.style
    await save_project(project_id, {"branding": brand, "current_step": "branding"})
    proj["branding"] = brand
    return _with_economy(serialize_doc(proj), meta)


# ----- BONUSES -----
@api.post("/projects/{project_id}/bonuses")
async def gen_bonuses(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opp = _require_pipeline(proj)
    # reuse ebook plan bonus generator via a light call
    from llm_service import llm_json, lang_name
    lang = lang_name(proj.get("product_language", "id"))
    system = f"You are a product bonus strategist. Write in {lang}."
    import json as _j
    prompt = (
        f"Opportunity: {_j.dumps(opp, ensure_ascii=False)}\n"
        f"Transformation: {(proj.get('transformation') or {}).get('core_transformation','')}\n"
        "Suggest 1-3 useful bonuses. Return JSON {\"bonuses\":[{\"title\":str,\"type\":str,\"description\":str}]}"
    )
    data = await llm_json("cheap", {}, system, prompt)
    return {"bonuses": data.get("bonuses", [])}


@api.post("/projects/{project_id}/ebook/bonus/{index}/generate")
async def ebook_bonus_generate(project_id: str, index: int, user: dict = Depends(get_current_user)):
    """Turn a planned bonus (e.g. 'Study Tracker') into an ACTUAL downloadable XLSX asset,
    using the same canonical palette as the rest of the product."""
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook:
        raise HTTPException(status_code=400, detail="No ebook yet")
    bonuses = ebook.get("bonuses", []) or []
    if index < 0 or index >= len(bonuses):
        raise HTTPException(status_code=404, detail="Bonus not found")
    bonus = bonuses[index]
    async def _do():
        spec = await agents.generate_bonus_asset_spec(bonus, ebook.get("meta", {}), proj.get("transformation"), proj.get("product_language", "id"), {})
        palette = (proj.get("transformation") or {}).get("palette", {})
        return exporters.build_xlsx(spec, palette)
    xlsx_bytes, meta = await run_ai(user, proj, "bonus", _do)
    safe = "".join([c if c.isalnum() else "_" for c in (bonus.get("title") or "bonus")])[:40] or f"bonus_{index}"
    asset = _register_asset(proj, "bonus", f"{safe}.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"bonus_{index}")
    bonus["asset_id"] = asset["id"]
    bonus["generated"] = True
    bonuses[index] = bonus
    ebook["bonuses"] = bonuses
    await save_project(project_id, {"ebook": ebook, "assets": proj["assets"]})
    proj["ebook"] = ebook
    return _with_economy(serialize_doc(proj), meta)


# ---------------------------------------------------------------------------
# Assets / downloads / website serving
# ---------------------------------------------------------------------------
# Asset types that belong in a downloadable product bundle, with folder names.
BUNDLE_ASSET_TYPES = {
    "pdf": "",            # main deliverable (ebook PDF) at root
    "xlsx": "",           # spreadsheet product at root
    "html": "website",    # website export
    "bonus": "bonuses",   # generated bonus XLSX files
}


def _safe_zip_name(existing: set, folder: str, filename: str) -> str:
    """Return a unique, path-safe name inside the zip (dedups collisions)."""
    filename = (filename or "file").replace("\\", "/").split("/")[-1] or "file"
    base = f"{folder}/{filename}" if folder else filename
    if base not in existing:
        existing.add(base)
        return base
    stem, dot, ext = filename.rpartition(".")
    i = 2
    while True:
        alt_name = f"{stem}_{i}.{ext}" if dot else f"{filename}_{i}"
        alt = f"{folder}/{alt_name}" if folder else alt_name
        if alt not in existing:
            existing.add(alt)
            return alt
        i += 1


@api.get("/projects/{project_id}/bundle")
async def download_bundle(project_id: str, user: dict = Depends(get_current_user)):
    """One-click 'Download Product Bundle' — packages all real downloadable
    assets of a product into a single ZIP, deterministically (NO AI).

    Ownership is enforced server-side: only the project owner (or admin) can
    download. Missing files are skipped gracefully; duplicate filenames are
    de-collided. Returns a real, usable ZIP."""
    proj = await load_project(project_id)
    # Ownership: owned projects require the owner; anonymous (unclaimed) projects
    # have no assets worth bundling (generation always claims), but guard anyway.
    owner = proj.get("user_id")
    if owner and owner != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You don't have access to this product's files.")

    assets = proj.get("assets", []) or []
    included, used_names = [], set()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for a in assets:
            atype = a.get("type")
            if atype not in BUNDLE_ASSET_TYPES:
                continue
            p = Path(a.get("path", ""))
            if not p.exists():
                continue  # missing file — skip gracefully
            try:
                data = p.read_bytes()
            except Exception:
                continue
            name = _safe_zip_name(used_names, BUNDLE_ASSET_TYPES[atype], a.get("filename"))
            zf.writestr(name, data)
            included.append({"type": atype, "name": name, "size": len(data)})

    if not included:
        raise HTTPException(status_code=400, detail="No downloadable assets yet. Generate and export your product first.")

    zip_bytes = buf.getvalue()
    title = proj.get("title") or "product"
    safe = "".join([c if c.isalnum() else "_" for c in str(title)])[:40] or "product"
    headers = {
        "Content-Disposition": f'attachment; filename="{safe}_bundle.zip"',
        "X-Bundle-Files": str(len(included)),
    }
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


@api.get("/projects/{project_id}/assets/{asset_id}/download")
async def download_asset(project_id: str, asset_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    for a in proj.get("assets", []) or []:
        if a["id"] == asset_id:
            p = Path(a["path"])
            if not p.exists():
                raise HTTPException(status_code=404, detail="Asset file missing")
            return FileResponse(str(p), media_type=a.get("mime"), filename=a.get("filename"))
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/api/sites/{slug}")
async def serve_site(slug: str, preview: int = 0):
    """Public site server.
    - Default: serves the PUBLISHED snapshot (stable shareable URL).
    - ?preview=1: serves the current DRAFT preview build (owner preview).
    Lookup by slug first, then fall back to project id."""
    proj = await db.projects.find_one({"website.slug": slug}, {"_id": 0})
    if not proj:
        proj = await db.projects.find_one({"id": slug}, {"_id": 0})
    web = (proj or {}).get("website") or {}
    if preview:
        html = web.get("draft_html")
        if not html and web.get("spec"):
            # build on the fly if a draft exists but was never previewed
            palette = (proj.get("transformation") or {}).get("palette", {})
            html = exporters.build_website_html(web["spec"], palette, web.get("style", "Modern"), proj.get("product_language", "id"))
        if not html:
            return HTMLResponse(content="<h1>Website draft not built yet</h1>", status_code=404)
        return HTMLResponse(content=html)
    published = web.get("published")
    if published and published.get("html") and published.get("live", True) is not False and web.get("status") == "published":
        return HTMLResponse(content=published["html"])
    return HTMLResponse(content="<h1>This website is not published.</h1>", status_code=404)


# ---------------------------------------------------------------------------
# Sample project (lightweight demo, no expensive assets)
# ---------------------------------------------------------------------------
@api.post("/projects/sample")
async def create_sample(user: Optional[dict] = Depends(get_optional_user)):
    from sample_data import build_sample_project
    doc = build_sample_project(user)
    await db.projects.insert_one(dict(doc))
    return serialize_doc(doc)


# ---------------------------------------------------------------------------
# Wire up
# ---------------------------------------------------------------------------
app.include_router(api)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup_indexes():
    await ratelimit.ensure_indexes()


@app.on_event("shutdown")
async def shutdown_db_client():
    from db import client
    client.close()
