"""Khova AI — FastAPI backend. AI digital product factory pipeline."""
import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import db, serialize_doc, GENERATED_DIR
from auth import auth_router, get_current_user, get_optional_user
import agents
import exporters
from llm_service import DEFAULT_MODELS, generate_image
from agents import build_cover_prompt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("khova")

app = FastAPI(title="Khova AI")
api = APIRouter(prefix="/api")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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
async def config_models():
    return {
        "providers": AVAILABLE_MODELS,
        "categories": AGENT_CATEGORIES,
        "defaults": {k: DEFAULT_MODELS[k] for k in AGENT_CATEGORIES},
        "note": "Research uses Gemini web-search grounding for real citations.",
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
    settings = {k: v for k, v in body.model_dump().items() if v is not None}
    if user:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"settings": settings}})
    return settings


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
async def run_research(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    bundle = await agents.run_market_research(proj.get("discover", {}), proj.get("product_language", "id"), proj.get("models_config", {}))
    bundle["generated_at"] = now_iso()
    await save_project(project_id, {"research": bundle, "current_step": "opportunities"})
    proj["research"] = bundle
    proj["current_step"] = "opportunities"
    return serialize_doc(proj)


@api.post("/projects/{project_id}/opportunities")
async def gen_opportunities(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    if not proj.get("research"):
        raise HTTPException(status_code=400, detail="Run market research first")
    opps = await agents.generate_opportunities(proj.get("discover", {}), proj["research"], proj.get("product_language", "id"), proj.get("models_config", {}))
    await save_project(project_id, {"opportunities": opps, "current_step": "opportunities"})
    proj["opportunities"] = opps
    return serialize_doc(proj)


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
async def gen_positioning(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opp = _selected_opp(proj)
    if not opp:
        raise HTTPException(status_code=400, detail="Select an opportunity first")
    pos = await agents.generate_positioning(opp, proj.get("discover", {}), proj.get("product_language", "id"), proj.get("models_config", {}))
    await save_project(project_id, {"positioning": pos, "current_step": "transformation"})
    proj["positioning"] = pos
    proj["current_step"] = "transformation"
    return serialize_doc(proj)


@api.post("/projects/{project_id}/transformation")
async def gen_transformation(project_id: str, user: Optional[dict] = Depends(get_optional_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    opp = _selected_opp(proj)
    if not opp or not proj.get("positioning"):
        raise HTTPException(status_code=400, detail="Positioning required first")
    tr = await agents.generate_transformation(opp, proj["positioning"], proj.get("product_language", "id"), proj.get("models_config", {}))
    # keep existing palette if set
    existing_palette = (proj.get("transformation") or {}).get("palette") if proj.get("transformation") else None
    tr["palette"] = existing_palette or {
        "primary": "#0B6E6B", "secondary": "#111C2E", "accent": "#C07A2B",
        "background": "#FBFAF7", "text": "#0B1220",
    }
    await save_project(project_id, {"transformation": tr, "current_step": "format"})
    proj["transformation"] = tr
    proj["current_step"] = "format"
    return serialize_doc(proj)


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
    plan = await agents.generate_ebook_plan(opp, proj["positioning"], proj["transformation"], proj.get("product_language", "id"), proj.get("models_config", {}))
    palette = (proj.get("transformation") or {}).get("palette", {})
    ebook = {
        "meta": plan.get("meta", {}),
        "toc": plan.get("toc", []),
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
        "progress": {"done": 0, "total": len(plan.get("toc", []))},
    }
    await save_project(project_id, {"ebook": ebook, "format": "ebook", "user_id": user["user_id"], "status": "creating"})
    proj["ebook"] = ebook
    return serialize_doc(proj)


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
    html = await agents.generate_ebook_section(chapter, ebook.get("meta", {}), proj.get("transformation"), proj.get("product_language", "id"), proj.get("models_config", {}), body.tone or "professional and clear")
    sections = [s for s in ebook.get("sections", []) if s.get("chapter_num") != body.chapter_num]
    sections.append({"chapter_num": body.chapter_num, "title": chapter.get("title"), "content_html": html, "status": "done"})
    sections.sort(key=lambda s: s.get("chapter_num", 0))
    ebook["sections"] = sections
    ebook["progress"] = {"done": len(sections), "total": len(ebook.get("toc", []))}
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return serialize_doc(proj)


@api.post("/projects/{project_id}/ebook/intro")
async def ebook_intro(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    ebook = proj.get("ebook")
    if not ebook:
        raise HTTPException(status_code=400, detail="Generate the ebook plan first")
    html = await agents.generate_introduction(ebook.get("meta", {}), proj.get("transformation"), proj.get("product_language", "id"), proj.get("models_config", {}))
    ebook["introduction_html"] = html
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return serialize_doc(proj)


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
    new_html = await agents.rewrite_section(sec["content_html"], body.instruction, proj.get("product_language", "id"), proj.get("models_config", {}))
    sec["content_html"] = new_html
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return serialize_doc(proj)


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
    data, mime = await generate_image(prompt, proj.get("models_config", {}))
    if not data:
        raise HTTPException(status_code=502, detail="Image generation failed. Please retry.")
    ext = "jpg" if "jpeg" in (mime or "") else "png"
    asset = _register_asset(proj, "cover", f"cover.{ext}", data, mime, key="cover")
    ebook["cover_asset_id"] = asset["id"]
    await save_project(project_id, {"ebook": ebook, "assets": proj["assets"]})
    return serialize_doc(proj)


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
    data, mime = await generate_image(full_prompt, proj.get("models_config", {}))
    if not data:
        raise HTTPException(status_code=502, detail="Image generation failed. Please retry.")
    ext = "jpg" if "jpeg" in (mime or "") else "png"
    asset = _register_asset(proj, "illustration", f"illo_{body.chapter_num}.{ext}", data, mime, key=f"ch{body.chapter_num}")
    illos = ebook.get("illustrations", {}) or {}
    illos[str(body.chapter_num)] = asset["id"]
    ebook["illustrations"] = illos
    await save_project(project_id, {"ebook": ebook, "assets": proj["assets"]})
    return serialize_doc(proj)


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
    html = exporters.build_ebook_html(ebook, proj.get("branding"), proj.get("transformation"), cover_bytes, cover_mime or "image/png", illustrations)
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
    html = exporters.build_ebook_html(ebook, proj.get("branding"), proj.get("transformation"), cover_bytes, cover_mime or "image/png", illustrations)
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
    spec = await agents.generate_spreadsheet_spec(opp, proj["positioning"], proj["transformation"], proj.get("product_language", "id"), proj.get("models_config", {}))
    ss = {"concept": spec.get("concept"), "product_type": spec.get("product_type"), "sheets": spec.get("sheets", []), "asset_id": None}
    await save_project(project_id, {"spreadsheet": ss, "format": "spreadsheet", "status": "creating"})
    proj["spreadsheet"] = ss
    return serialize_doc(proj)


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


# ----- WEBSITE -----
class WebsiteStyleBody(BaseModel):
    style: str = "Modern"


@api.post("/projects/{project_id}/website/spec")
async def website_spec(project_id: str, body: WebsiteStyleBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    spec = await agents.generate_website_spec(opp, proj["positioning"], proj["transformation"], body.style, proj.get("product_language", "id"), proj.get("models_config", {}))
    web = {"style": body.style, "spec": spec, "html": None, "asset_id": None}
    await save_project(project_id, {"website": web, "format": "website", "status": "creating"})
    proj["website"] = web
    return serialize_doc(proj)


@api.post("/projects/{project_id}/website/build")
async def website_build(project_id: str, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    web = proj.get("website")
    if not web or not web.get("spec"):
        raise HTTPException(status_code=400, detail="Generate the website spec first")
    palette = (proj.get("transformation") or {}).get("palette", {})
    html = exporters.build_website_html(web["spec"], palette, web.get("style", "Modern"))
    web["html"] = html
    asset = _register_asset(proj, "html", "website.html", html.encode("utf-8"), "text/html", key="website")
    web["asset_id"] = asset["id"]
    await save_project(project_id, {"website": web, "assets": proj["assets"], "status": "complete", "current_step": "export"})
    return {"project": serialize_doc(proj), "asset": asset, "url": f"/api/sites/{project_id}"}


class WebsiteEditBody(BaseModel):
    spec: Dict[str, Any]


@api.patch("/projects/{project_id}/website/spec")
async def website_edit(project_id: str, body: WebsiteEditBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    web = proj.get("website") or {}
    web["spec"] = body.spec
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
    report = await agents.qa_review(fmt, content, proj.get("transformation"), proj.get("product_language", "id"), proj.get("models_config", {}))
    report["format"] = fmt
    report["created_at"] = now_iso()
    report["id"] = f"qa_{uuid.uuid4().hex[:8]}"
    qa = proj.get("qa", []) or []
    qa.insert(0, report)
    await save_project(project_id, {"qa": qa, "current_step": "qa"})
    proj["qa"] = qa
    return serialize_doc(proj)


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
    # keep originals as versions
    for sec in ebook.get("sections", []):
        original = sec["content_html"]
        new_html = await agents.rewrite_section(original, f"Apply these QA improvements: {improvements}", proj.get("product_language", "id"), proj.get("models_config", {}))
        sec.setdefault("versions", []).append({"content_html": original, "saved_at": now_iso()})
        sec["content_html"] = new_html
    await save_project(project_id, {"ebook": ebook})
    proj["ebook"] = ebook
    return serialize_doc(proj)


# ----- BRANDING -----
class BrandingBody(BaseModel):
    style: str = "Premium"


@api.post("/projects/{project_id}/branding")
async def gen_branding(project_id: str, body: BrandingBody, user: dict = Depends(get_current_user)):
    proj = await load_project(project_id)
    check_access(proj, user)
    await claim_if_needed(proj, user)
    opp = _require_pipeline(proj)
    brand = await agents.generate_branding(opp, proj["positioning"], proj["transformation"], body.style, proj.get("product_language", "id"), proj.get("models_config", {}))
    brand["style"] = body.style
    await save_project(project_id, {"branding": brand, "current_step": "branding"})
    proj["branding"] = brand
    return serialize_doc(proj)


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
    data = await llm_json("cheap", proj.get("models_config", {}), system, prompt)
    return {"bonuses": data.get("bonuses", [])}


# ---------------------------------------------------------------------------
# Assets / downloads / website serving
# ---------------------------------------------------------------------------
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


@app.get("/api/sites/{project_id}")
async def serve_site(project_id: str):
    proj = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not proj or not proj.get("website") or not proj["website"].get("html"):
        return HTMLResponse(content="<h1>Website not generated yet</h1>", status_code=404)
    return HTMLResponse(content=proj["website"]["html"])


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


@app.on_event("shutdown")
async def shutdown_db_client():
    from db import client
    client.close()
