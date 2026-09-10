"""Provider-abstracted LLM service for Khova AI.

Wraps emergentintegrations LlmChat with:
  - llm_json / llm_text (multi-provider, per-category model config)
  - research() using Gemini googleSearch grounding -> text + real citations
  - generate_image() using Nano Banana
"""
import os
import re
import json
import uuid
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv

from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
API_KEY = os.getenv("EMERGENT_LLM_KEY")
logger = logging.getLogger("khova.llm")

# Default model per agent category. Fast/cheap tier for volume tasks, strong for quality.
DEFAULT_MODELS = {
    "research": {"provider": "gemini", "model": "gemini-2.5-flash"},
    "opportunities": {"provider": "gemini", "model": "gemini-2.5-flash"},
    "strategy": {"provider": "openai", "model": "gpt-5.4"},
    "writing": {"provider": "openai", "model": "gpt-5.4"},
    "qa": {"provider": "openai", "model": "gpt-5.4"},
    "cheap": {"provider": "openai", "model": "gpt-5.4-mini"},
    "image": {"provider": "gemini", "model": "gemini-3.1-flash-image-preview"},
}

LANG_NAMES = {
    "id": "Indonesian (Bahasa Indonesia)",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get((code or "id").lower(), code or "Indonesian")


# Languages actually covered by the structural label tables (agents.SECTION_LABELS,
# exporters.LABELS), as opposed to LANG_NAMES above (which also lists zh/ar/hi that
# those tables don't yet support). This is the single source of truth used to
# validate product_language/ui_language at the API boundary — see server.py.
SUPPORTED_LANGUAGES = frozenset({"id", "en", "es", "fr", "de", "pt", "ja"})


def _resolve(category: str, models_config: dict):
    cfg = (models_config or {}).get(category) if models_config else None
    if cfg and cfg.get("provider") and cfg.get("model"):
        return cfg["provider"], cfg["model"]
    d = DEFAULT_MODELS.get(category, DEFAULT_MODELS["strategy"])
    return d["provider"], d["model"]


def _chat(category, models_config, system):
    provider, model = _resolve(category, models_config)
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"khova-{category}-{uuid.uuid4().hex[:8]}",
        system_message=system,
    ).with_model(provider, model)
    return chat


def extract_json(text: str):
    if not text:
        raise ValueError("empty response")
    t = text.strip()
    # strip code fences
    if "```" in t:
        m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
        if m:
            t = m.group(1).strip()
    # find outermost braces or brackets
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = t.find(open_c)
        end = t.rfind(close_c)
        if start != -1 and end != -1 and end > start:
            candidate = t[start:end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                continue
    return json.loads(t)


async def llm_text(category, models_config, system, prompt) -> str:
    chat = _chat(category, models_config, system)
    resp = await chat.send_message(UserMessage(text=prompt))
    return resp or ""


async def llm_json(category, models_config, system, prompt, retries: int = 1):
    sys = system + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown fences, no commentary before or after."
    last_err = None
    for attempt in range(retries + 1):
        chat = _chat(category, models_config, sys)
        p = prompt if attempt == 0 else prompt + "\n\nYour previous response was not valid JSON. Return ONLY valid JSON this time."
        try:
            resp = await chat.send_message(UserMessage(text=p))
            return extract_json(resp)
        except Exception as e:
            last_err = e
            logger.warning(f"llm_json parse failed (attempt {attempt}): {e}")
    raise ValueError(f"Failed to get valid JSON after {retries+1} attempts: {last_err}")


def _extract_citations(raw) -> list:
    sources = []
    try:
        choice = raw["choices"][0] if isinstance(raw, dict) else raw.choices[0]
        msg = choice["message"] if isinstance(choice, dict) else choice.message
        anns = (msg.get("annotations") if isinstance(msg, dict) else getattr(msg, "annotations", None)) or []
        for a in anns:
            if isinstance(a, dict):
                uc = a.get("url_citation") or a
                url = uc.get("url")
                title = uc.get("title")
                if url:
                    sources.append({"title": title or url, "url": url})
    except Exception as e:
        logger.info(f"annotation extract note: {e}")
    if not sources:
        try:
            choice = raw["choices"][0] if isinstance(raw, dict) else raw.choices[0]
            gm = None
            if isinstance(choice, dict):
                gm = choice.get("groundingMetadata") or (choice.get("message", {}) or {}).get("groundingMetadata")
            else:
                gm = getattr(choice, "groundingMetadata", None)
            if gm:
                chunks = gm.get("groundingChunks", []) if isinstance(gm, dict) else getattr(gm, "groundingChunks", [])
                for c in chunks:
                    web = c.get("web") if isinstance(c, dict) else getattr(c, "web", None)
                    if web:
                        url = web.get("uri") if isinstance(web, dict) else getattr(web, "uri", None)
                        title = web.get("title") if isinstance(web, dict) else getattr(web, "title", None)
                        if url:
                            sources.append({"title": title or url, "url": url})
        except Exception as e:
            logger.info(f"grounding extract note: {e}")
    # dedupe by url
    seen = set()
    out = []
    for s in sources:
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        out.append(s)
    return out


async def research(models_config, query: str, product_language: str):
    """Run provider-hosted web search. Returns {text, sources, available}.
    Uses Gemini googleSearch grounding (best citations via Emergent key).
    """
    provider, model = _resolve("research", models_config)
    lang = lang_name(product_language)
    system = (
        "You are an elite market researcher. Use web search to gather CURRENT, REAL information. "
        "Never fabricate sources or statistics. Distinguish clearly between what you verified via search "
        f"and what is your own hypothesis. Write your findings in {lang}."
    )
    try:
        if provider == "gemini":
            chat = LlmChat(api_key=API_KEY, session_id=f"khova-research-{uuid.uuid4().hex[:8]}",
                           system_message=system).with_model("gemini", model).with_tools([{"googleSearch": {}}])
        elif provider == "anthropic":
            chat = LlmChat(api_key=API_KEY, session_id=f"khova-research-{uuid.uuid4().hex[:8]}",
                           system_message=system).with_model("anthropic", model).with_tools(
                [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}])
        else:
            # fallback to gemini grounding
            chat = LlmChat(api_key=API_KEY, session_id=f"khova-research-{uuid.uuid4().hex[:8]}",
                           system_message=system).with_model("gemini", "gemini-2.5-flash").with_tools([{"googleSearch": {}}])
        resp = await chat.send_message_with_tools(UserMessage(text=query))
        text = getattr(resp, "content", None) or ""
        raw = getattr(resp, "raw", None)
        sources = _extract_citations(raw) if raw is not None else []
        return {"text": text, "sources": sources, "available": bool(text)}
    except Exception as e:
        logger.error(f"research failed: {e}")
        return {"text": "", "sources": [], "available": False, "error": str(e)}


async def generate_image(prompt: str, models_config=None):
    """Generate an image via Nano Banana. Returns (bytes, mime) or (None, None)."""
    provider, model = _resolve("image", models_config)
    try:
        chat = LlmChat(api_key=API_KEY, session_id=f"khova-img-{uuid.uuid4().hex[:8]}",
                       system_message="You are a professional visual designer producing clean, premium graphics.")
        chat = chat.with_model("gemini", model).with_params(modalities=["image", "text"])
        text, images = await chat.send_message_multimodal_response(UserMessage(text=prompt))
        if images and len(images) > 0:
            img = images[0]
            return base64.b64decode(img["data"]), img.get("mime_type", "image/png")
    except Exception as e:
        logger.error(f"image gen failed: {e}")
    return None, None
