"""Internal model routing for Khova AI.

Users NEVER select an AI provider or model. Khova decides which provider/model/
tier to use per task based on complexity, expected quality and cost. This module
is the single source of truth for that routing so the rest of the app (jobs,
admin, usage logging) can record what was actually used without exposing it to
normal users.
"""
from llm_service import DEFAULT_MODELS

# --- Task complexity tiers -------------------------------------------------
# LOW  : classification / metadata / formatting / simple scoring / light ops
# MID  : opportunity generation / planning / standard writing / website content
# HIGH : deep research synthesis / long-form manuscript / complex strategy / QA
TASK_TIER = {
    "research": "high",
    "opportunities": "mid",
    "positioning": "mid",
    "transformation": "mid",
    "ebook_plan": "high",
    "ebook_section": "high",
    "ebook_intro": "mid",
    "ebook_rewrite": "mid",
    "qa": "high",
    "qa_apply": "high",
    "branding": "low",
    "spreadsheet_spec": "mid",
    "website_spec": "mid",
    "website_section": "mid",
    "bonus": "mid",
    "cover": "mid",
    "illustration": "mid",
    "cheap": "low",
}

# Tier -> the llm_service category whose DEFAULT_MODELS entry we use.
# (Research keeps its own grounding-capable model inside llm_service.research.)
TIER_CATEGORY = {
    "low": "cheap",         # gpt-5.4-mini
    "mid": "opportunities", # gemini flash (fast, economical)
    "high": "writing",      # gpt-5.4 (strong reasoning / long-form)
}

# Image tasks always route to the image model.
IMAGE_TASKS = {"cover", "illustration"}


def tier_for(task: str) -> str:
    return TASK_TIER.get(task, "mid")


def route(task: str) -> dict:
    """Return the internal routing decision for a task.

    Returns {tier, category, provider, model}. Never surfaced to normal users;
    used for generation-job records, admin monitoring and usage logging.
    """
    if task in IMAGE_TASKS:
        d = DEFAULT_MODELS["image"]
        return {"tier": tier_for(task), "category": "image", "provider": d["provider"], "model": d["model"]}
    tier = tier_for(task)
    category = TIER_CATEGORY.get(tier, "opportunities")
    if task == "research":
        category = "research"
    d = DEFAULT_MODELS.get(category, DEFAULT_MODELS["strategy"])
    return {"tier": tier, "category": category, "provider": d["provider"], "model": d["model"]}


def user_facing_message(task: str) -> str:
    """A friendly, provider-agnostic status message for the UI."""
    return "Khova AI is selecting the best model for this task."
