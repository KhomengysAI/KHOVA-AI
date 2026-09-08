"""Specialized AI agents for Khova AI. Each function has one responsibility and
returns structured data. Product language is enforced on every generation.
"""
import json
import logging
import uuid

from llm_service import llm_json, llm_text, research, lang_name

logger = logging.getLogger("khova.agents")


def _uid(prefix="op"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _discover_summary(discover: dict) -> str:
    d = discover or {}
    parts = []
    fields = [
        ("mode", "Mode"), ("idea", "Idea"), ("expertise", "Expertise"),
        ("experience", "Experience"), ("audience", "Target audience"),
        ("interests", "Interests"), ("skills", "Skills"), ("story", "Personal story"),
        ("problem", "Problem they understand"), ("framework", "Existing framework"),
        ("industry", "Desired industry"), ("preferred_audience", "Preferred audience"),
    ]
    for key, label in fields:
        v = d.get(key)
        if v:
            parts.append(f"{label}: {v}")
    uploads = d.get("uploads") or []
    for u in uploads:
        if u.get("text"):
            parts.append(f"Reference material '{u.get('name','file')}' (excerpt): {u['text'][:1200]}")
    if not parts:
        return "The user provided almost no context."
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1. MARKET RESEARCH
# ---------------------------------------------------------------------------
async def run_market_research(discover: dict, product_language: str, models_config: dict):
    lang = lang_name(product_language)
    ctx = _discover_summary(discover)
    query = (
        "Perform real-time market research for a potential DIGITAL PRODUCT based on this creator context:\n"
        f"{ctx}\n\n"
        "Investigate publicly available information: existing digital products (ebooks, templates, spreadsheets, "
        "courses, toolkits), competitors, product marketplaces, pricing, customer reviews, community discussions "
        "(Reddit/forums), FAQs, common complaints, unmet needs, recurring pain points, product gaps and positioning. "
        "Find: (1) what people already buy, (2) what they repeatedly complain about, (3) what outcomes they want, "
        "(4) what existing products fail to solve, (5) what competitors emphasize, (6) where there is an opportunity "
        "for a better/different product. Cite specific products, prices, and quotes where possible."
    )
    res = await research(models_config, query, product_language)

    if not res.get("available"):
        return {
            "status": "unavailable",
            "summary": "",
            "findings": [],
            "sources": [],
            "note": "Real-time web research could not be completed. Findings below are AI hypotheses/assumptions, not verified.",
        }

    sources_list = "\n".join([f"- {s['title']} ({s['url']})" for s in res["sources"][:25]]) or "(no explicit citations returned)"
    synth_system = (
        f"You are a market research analyst. Write all output in {lang}. "
        "You will structure raw web-research notes into clean findings. Label each finding honestly."
    )
    synth_prompt = (
        "Here are raw web research notes gathered via live search:\n\n"
        f"=== RESEARCH NOTES ===\n{res['text'][:9000]}\n\n"
        f"=== SOURCES FOUND ===\n{sources_list}\n\n"
        "Produce a JSON object with this exact shape:\n"
        "{\n"
        '  \"summary\": \"3-5 sentence executive summary of the market\",\n'
        '  \"findings\": [\n'
        '    {\"text\": \"specific finding\", \"label\": \"RESEARCH-BACKED|HYPOTHESIS|ASSUMPTION\", \"relevance\": \"why it matters for product creation\"}\n'
        "  ],\n"
        '  \"pain_points\": [\"...\"],\n'
        '  \"what_people_buy\": [\"...\"],\n'
        '  \"gaps\": [\"...\"]\n'
        "}\n"
        "Rules: Mark a finding RESEARCH-BACKED only if it is supported by the notes/sources above. "
        "Mark reasonable inferences as HYPOTHESIS, and speculative ideas as ASSUMPTION. Never invent sources. "
        "Return 8-14 findings."
    )
    try:
        structured = await llm_json("cheap", models_config, synth_system, synth_prompt)
    except Exception as e:
        logger.error(f"research synthesis failed: {e}")
        structured = {"summary": res["text"][:600], "findings": [], "pain_points": [], "what_people_buy": [], "gaps": []}

    return {
        "status": "complete",
        "summary": structured.get("summary", ""),
        "findings": structured.get("findings", []),
        "pain_points": structured.get("pain_points", []),
        "what_people_buy": structured.get("what_people_buy", []),
        "gaps": structured.get("gaps", []),
        "sources": res["sources"],
        "raw_notes": res["text"][:6000],
    }


# ---------------------------------------------------------------------------
# 2. PROFITABLE POCKETS (opportunities)
# ---------------------------------------------------------------------------
async def generate_opportunities(discover: dict, research_bundle: dict, product_language: str, models_config: dict, count: int = 20):
    lang = lang_name(product_language)
    ctx = _discover_summary(discover)
    findings = json.dumps(research_bundle.get("findings", [])[:14], ensure_ascii=False)
    summary = research_bundle.get("summary", "")
    gaps = json.dumps(research_bundle.get("gaps", []), ensure_ascii=False)

    system = (
        f"You are an elite opportunity researcher for digital products. Write all output in {lang}. "
        "Generate market-informed, differentiated opportunities. Reuse the provided research; do NOT invent sources."
    )
    prompt = (
        f"Creator context:\n{ctx}\n\n"
        f"Market research summary: {summary}\n"
        f"Key findings: {findings}\n"
        f"Product gaps: {gaps}\n\n"
        f"Generate approximately {count} market-validated 'profitable pocket' opportunities. Prioritize quality and variety. "
        "Return a JSON object: {\"opportunities\": [ ... ]}. Each opportunity object MUST have:\n"
        "{\n"
        '  \"name\": str,\n'
        '  \"target_customer\": str,\n'
        '  \"problem\": str,\n'
        '  \"desired_outcome\": str,\n'
        '  \"industry\": str,\n'
        '  \"niche\": str,\n'
        '  \"existing_alternatives\": str,\n'
        '  \"market_evidence\": str,\n'
        '  \"product_gap\": str,\n'
        '  \"product_concept\": str,\n'
        '  \"scores\": {\"pain\": 1-10, \"worsening\": 1-10, \"purchasing_power\": 1-10, \"speed\": 1-10, \"market_validation\": 1-10, \"differentiation\": 1-10}\n'
        "}\n"
        "Scores meaning: pain=how painful; worsening=is it becoming more urgent; purchasing_power=does audience spend money; "
        "speed=can customer get a fast result; market_validation=evidence people already buy; differentiation=can we be meaningfully different. "
        "Keep each text field concise (1-2 sentences). Return valid JSON only."
    )
    data = await llm_json("opportunities", models_config, system, prompt)
    opps = data.get("opportunities", data if isinstance(data, list) else [])
    result = []
    for o in opps:
        scores = o.get("scores", {}) or {}
        keys = ["pain", "worsening", "purchasing_power", "speed", "market_validation", "differentiation"]
        vals = []
        clean_scores = {}
        for k in keys:
            v = scores.get(k, 5)
            try:
                v = int(round(float(v)))
            except Exception:
                v = 5
            v = max(1, min(10, v))
            clean_scores[k] = v
            vals.append(v)
        overall = round(sum(vals) / len(vals), 1) if vals else 5.0
        result.append({
            "id": _uid("op"),
            "name": o.get("name", "Untitled Opportunity"),
            "target_customer": o.get("target_customer", ""),
            "problem": o.get("problem", ""),
            "desired_outcome": o.get("desired_outcome", ""),
            "industry": o.get("industry", ""),
            "niche": o.get("niche", ""),
            "existing_alternatives": o.get("existing_alternatives", ""),
            "market_evidence": o.get("market_evidence", ""),
            "product_gap": o.get("product_gap", ""),
            "product_concept": o.get("product_concept", ""),
            "scores": clean_scores,
            "overall_score": overall,
            "saved": False,
        })
    result.sort(key=lambda x: x["overall_score"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# 3. PRODUCT POSITIONING
# ---------------------------------------------------------------------------
async def generate_positioning(opportunity: dict, discover: dict, product_language: str, models_config: dict):
    lang = lang_name(product_language)
    system = f"You are a world-class product strategist. Write all output in {lang}."
    prompt = (
        f"Selected opportunity:\n{json.dumps(opportunity, ensure_ascii=False)}\n\n"
        "Create a product strategy as JSON with keys:\n"
        "{\n"
        '  \"target_customer\": str,\n'
        '  \"problem\": str,\n'
        '  \"desired_result\": str,\n'
        '  \"unique_angle\": str,\n'
        '  \"positioning\": str,\n'
        '  \"product_promise\": str,\n'
        '  \"mechanism\": str,\n'
        '  \"suggested_pricing\": str,\n'
        '  \"why_choose\": str,\n'
        '  \"alternatives\": str,\n'
        '  \"competitive_differentiation\": str,\n'
        '  \"one_liner\": \"a single sentence following the pattern: I help [customer] achieve [result] without [major obstacle]\"\n'
        "}\n"
        f"IMPORTANT: Write EVERY value (including the one_liner) fully in {lang}. "
        "Translate the one_liner pattern naturally into that language (do NOT leave English words like 'I help/achieve/without'). "
        "Return valid JSON only."
    )
    return await llm_json("strategy", models_config, system, prompt)


# ---------------------------------------------------------------------------
# 4. VISCERAL TRANSFORMATION MAP
# ---------------------------------------------------------------------------
async def generate_transformation(opportunity: dict, positioning: dict, product_language: str, models_config: dict):
    lang = lang_name(product_language)
    system = f"You are a transformation strategist. Write all output in {lang}. Be specific, believable and emotionally recognizable; avoid vague claims."
    prompt = (
        f"Opportunity: {json.dumps(opportunity, ensure_ascii=False)}\n"
        f"Positioning: {json.dumps(positioning, ensure_ascii=False)}\n\n"
        "Create a Visceral Transformation Map as JSON:\n"
        "{\n"
        '  \"categories\": [\n'
        '    {\"key\": \"emotional_state\", \"label\": \"Emotional State\", \"before\": str, \"after\": str},\n'
        '    {\"key\": \"core_fear\", \"label\": \"Core Fear\", \"before\": str, \"after\": str},\n'
        '    {\"key\": \"daily_experience\", \"label\": \"Daily Experience\", \"before\": str, \"after\": str},\n'
        '    {\"key\": \"identity\", \"label\": \"Identity\", \"before\": str, \"after\": str},\n'
        '    {\"key\": \"practical_situation\", \"label\": \"Practical Situation\", \"before\": str, \"after\": str},\n'
        '    {\"key\": \"desired_outcome\", \"label\": \"Desired Outcome\", \"before\": str, \"after\": str}\n'
        "  ],\n"
        '  \"core_transformation\": str,\n'
        '  \"core_promise\": str,\n'
        '  \"customer_win\": str\n'
        "}\nReturn valid JSON only."
    )
    return await llm_json("strategy", models_config, system, prompt)


# ---------------------------------------------------------------------------
# 8. EBOOK PLANNER
# ---------------------------------------------------------------------------
async def generate_ebook_plan(opportunity, positioning, transformation, product_language, models_config, palette=None):
    lang = lang_name(product_language)
    system = f"You are a senior ebook editor and instructional designer. Write all output in {lang}."
    prompt = (
        f"Opportunity: {json.dumps(opportunity, ensure_ascii=False)}\n"
        f"Positioning: {json.dumps(positioning, ensure_ascii=False)}\n"
        f"Transformation: {json.dumps(transformation, ensure_ascii=False)}\n\n"
        "Plan a premium, genuinely useful ebook. Return JSON:\n"
        "{\n"
        '  \"meta\": {\"title\": str, \"subtitle\": str, \"audience\": str, \"core_promise\": str, \"description\": str,\n'
        '            \"learning_outcomes\": [str], \"reading_time\": str, \"chapter_count\": int},\n'
        '  \"toc\": [ {\"chapter_num\": 1, \"title\": str, \"purpose\": str, \"key_lesson\": str} ],\n'
        '  \"visuals\": [ {\"chapter_num\": 1, \"purpose\": str, \"visual_type\": \"illustration|diagram|infographic|chart|icon\", \"prompt\": \"detailed image generation prompt\"} ],\n'
        '  \"bonuses\": [ {\"title\": str, \"type\": \"checklist|worksheet|action_plan|prompt_library|template|quick_start\", \"description\": str} ]\n'
        "}\n"
        "Rules: 6-10 chapters unless the topic clearly needs otherwise. Suggest 2-4 visuals total (only where they add real value). "
        "Suggest 1-3 relevant bonuses. Return valid JSON only."
    )
    plan = await llm_json("strategy", models_config, system, prompt)
    # attach ids to toc/sections
    toc = plan.get("toc", [])
    for i, ch in enumerate(toc, start=1):
        ch["chapter_num"] = ch.get("chapter_num", i)
    return plan


async def generate_ebook_section(chapter, ebook_meta, transformation, product_language, models_config, tone="professional and clear"):
    lang = lang_name(product_language)
    system = (
        f"You are an expert non-fiction author. Write all output in {lang}. Tone: {tone}. "
        "Write original, useful, specific content. NO filler, NO generic AI prose, NO repetition. "
        "Use concrete examples, frameworks, and practical steps. Flag any claim needing verification with [verify]."
    )
    prompt = (
        f"Ebook: {ebook_meta.get('title','')} — {ebook_meta.get('subtitle','')}\n"
        f"Audience: {ebook_meta.get('audience','')}\n"
        f"Core promise: {ebook_meta.get('core_promise','')}\n"
        f"Core transformation: {transformation.get('core_transformation','') if transformation else ''}\n\n"
        f"Write chapter {chapter.get('chapter_num')}: \"{chapter.get('title')}\".\n"
        f"Chapter purpose: {chapter.get('purpose','')}. Key lesson: {chapter.get('key_lesson','')}.\n\n"
        "Return ONLY clean semantic HTML (no <html>/<body> wrapper, no markdown). Use these building blocks where appropriate:\n"
        "  <p>...</p> for prose\n"
        "  <h3>...</h3> for subheadings\n"
        "  <ul><li>...</li></ul> for lists\n"
        "  <table>...</table> for useful tables\n"
        "  <div class=\"callout\"><strong>Key idea:</strong> ...</div> for important callouts\n"
        "  <div class=\"example\"><strong>Example:</strong> ...</div> for concrete examples\n"
        "  <div class=\"action-steps\"><h4>Action Steps</h4><ol><li>...</li></ol></div>\n"
        "  <div class=\"exercise\"><h4>Exercise</h4>...</div> (when appropriate)\n"
        "  <div class=\"summary\"><h4>Summary</h4>...</div> at the end.\n"
        "Aim for 700-1100 words of substantive content. Do not include the chapter title as an <h2> (it is added automatically)."
    )
    html = await llm_text("writing", models_config, system, prompt)
    # strip accidental code fences / html wrapper
    html = html.strip()
    if html.startswith("```"):
        html = html.split("```", 2)[1]
        if html.lstrip().lower().startswith("html"):
            html = html.lstrip()[4:]
    for tag in ["<!DOCTYPE html>", "<html>", "</html>", "<body>", "</body>", "<head>", "</head>"]:
        html = html.replace(tag, "")
    return html.strip()


async def rewrite_section(existing_html, instruction, product_language, models_config):
    lang = lang_name(product_language)
    system = f"You are an expert editor. Write all output in {lang}. Keep the same clean HTML block style."
    prompt = (
        f"Instruction: {instruction}\n\nCurrent chapter HTML:\n{existing_html}\n\n"
        "Return the improved chapter as clean semantic HTML only (no markdown, no html/body wrapper)."
    )
    html = await llm_text("writing", models_config, system, prompt)
    html = html.strip()
    if html.startswith("```"):
        html = html.split("```", 2)[1]
        if html.lstrip().lower().startswith("html"):
            html = html.lstrip()[4:]
    return html.strip()


async def generate_introduction(ebook_meta, transformation, product_language, models_config):
    lang = lang_name(product_language)
    system = f"You are an expert author. Write all output in {lang}."
    prompt = (
        f"Write a compelling 250-400 word introduction for the ebook '{ebook_meta.get('title','')}'. "
        f"Audience: {ebook_meta.get('audience','')}. Promise: {ebook_meta.get('core_promise','')}. "
        f"Core transformation: {transformation.get('core_transformation','') if transformation else ''}. "
        "Return clean HTML paragraphs only (no wrapper, no markdown)."
    )
    html = await llm_text("writing", models_config, system, prompt)
    return html.strip()


# ---------------------------------------------------------------------------
# 10. SPREADSHEET CREATOR
# ---------------------------------------------------------------------------
async def generate_spreadsheet_spec(opportunity, positioning, transformation, product_language, models_config):
    lang = lang_name(product_language)
    system = (
        f"You are a spreadsheet product designer. Write all labels/instructions in {lang}. "
        "Design a genuinely useful spreadsheet tool (planner/tracker/calculator/dashboard) around the transformation. "
        "Do NOT just place text into cells."
    )
    prompt = (
        f"Opportunity: {json.dumps(opportunity, ensure_ascii=False)}\n"
        f"Positioning: {json.dumps(positioning, ensure_ascii=False)}\n"
        f"Transformation core: {transformation.get('core_transformation','') if transformation else ''}\n\n"
        "Return JSON describing a multi-sheet workbook:\n"
        "{\n"
        '  \"concept\": str,\n'
        '  \"product_type\": \"Budget Planner|Study Planner|Business Calculator|Habit Tracker|Content Planner|Project Tracker|Financial Model|Inventory Tracker|Other\",\n'
        '  \"sheets\": [\n'
        "    {\n"
        '      \"name\": str,\n'
        '      \"purpose\": str,\n'
        '      \"instructions\": str,\n'
        '      \"columns\": [ {\"header\": str, \"type\": \"text|number|currency|percent|date|formula\", \"formula_template\": \"=B{r}-C{r} (only if type=formula, use {r} for current row)\", \"dropdown\": [\"opt1\",\"opt2\"] } ],\n'
        '      \"example_rows\": [ [\"cell1\", 123, 456] ],\n'
        '      \"totals\": [ {\"label\": str, \"col_index\": 1, \"formula\": \"=SUM(B{first}:B{last})\"} ]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules: 2-4 sheets (include one Instructions/summary sheet). example_rows are arrays aligned to columns order. "
        "For formula columns give formula_template using {r} for the row. For totals use {first}/{last} row placeholders and Excel column letters. "
        "Provide 3-8 example rows per data sheet. Return valid JSON only."
    )
    return await llm_json("strategy", models_config, system, prompt)


# ---------------------------------------------------------------------------
# 11. WEBSITE CREATOR
# ---------------------------------------------------------------------------
async def generate_website_spec(opportunity, positioning, transformation, style, product_language, models_config):
    lang = lang_name(product_language)
    system = f"You are a conversion copywriter and web designer. Write all copy in {lang}. Style: {style}."
    prompt = (
        f"Opportunity: {json.dumps(opportunity, ensure_ascii=False)}\n"
        f"Positioning: {json.dumps(positioning, ensure_ascii=False)}\n"
        f"Transformation: {json.dumps(transformation, ensure_ascii=False)}\n\n"
        "Create a conversion-focused landing page as JSON:\n"
        "{\n"
        '  \"brand\": str,\n'
        '  \"hero\": {\"headline\": str, \"subheadline\": str, \"cta\": str},\n'
        '  \"problem\": {\"title\": str, \"body\": str, \"bullets\": [str]},\n'
        '  \"transformation\": {\"title\": str, \"before\": [str], \"after\": [str]},\n'
        '  \"benefits\": {\"title\": str, \"items\": [{\"title\": str, \"desc\": str}]},\n'
        '  \"whats_included\": {\"title\": str, \"items\": [str]},\n'
        '  \"how_it_works\": {\"title\": str, \"steps\": [{\"title\": str, \"desc\": str}]},\n'
        '  \"social_proof\": {\"title\": str, \"placeholder\": str},\n'
        '  \"faq\": {\"title\": str, \"items\": [{\"q\": str, \"a\": str}]},\n'
        '  \"final_cta\": {\"headline\": str, \"cta\": str}\n'
        "}\nReturn valid JSON only."
    )
    return await llm_json("strategy", models_config, system, prompt)


# ---------------------------------------------------------------------------
# 14. CONTENT QA
# ---------------------------------------------------------------------------
async def qa_review(format_type, content_text, transformation, product_language, models_config):
    lang = lang_name(product_language)
    system = f"You are a rigorous content QA editor. Write all output in {lang}."
    prompt = (
        f"Review this {format_type} product content for quality.\n\n"
        f"Content (may be truncated):\n{content_text[:9000]}\n\n"
        f"Transformation to align with: {transformation.get('core_transformation','') if transformation else ''}\n\n"
        "Return JSON:\n"
        "{\n"
        '  \"scores\": {\"clarity\": 1-10, \"logic\": 1-10, \"usefulness\": 1-10, \"originality\": 1-10, \"formatting\": 1-10, \"transformation_alignment\": 1-10},\n'
        '  \"overall\": 1-10,\n'
        '  \"issues\": [ {\"type\": \"contradiction|repetition|weak_explanation|missing_content|poor_logic|unsupported_claim|unclear_instruction|ai_sounding|formatting\", \"severity\": \"low|medium|high\", \"detail\": str, \"fix\": str} ],\n'
        '  \"recommended_improvements\": [str]\n'
        "}\nReturn valid JSON only."
    )
    return await llm_json("qa", models_config, system, prompt)


# ---------------------------------------------------------------------------
# 15. BRANDING
# ---------------------------------------------------------------------------
async def generate_branding(opportunity, positioning, transformation, style, product_language, models_config):
    lang = lang_name(product_language)
    system = f"You are a brand designer. Write all output in {lang}. Style: {style}."
    prompt = (
        f"Opportunity: {json.dumps(opportunity, ensure_ascii=False)}\n"
        f"Positioning: {json.dumps(positioning, ensure_ascii=False)}\n\n"
        "Create branding as JSON:\n"
        "{\n"
        '  \"title\": str, \"subtitle\": str, \"author\": str, \"brand\": str, \"description\": str,\n'
        '  \"visual_direction\": str, \"typography\": str, \"tone\": str,\n'
        '  \"colors\": [ {\"name\": str, \"hex\": \"#RRGGBB\"} ],\n'
        '  \"cover_concept\": str\n'
        "}\nProvide 4-5 harmonious colors with exact HEX. Return valid JSON only."
    )
    return await llm_json("strategy", models_config, system, prompt)


def build_cover_prompt(branding, ebook_meta, palette):
    colors = ""
    if palette:
        colors = ", ".join([f"{k}: {v}" for k, v in palette.items() if v])
    elif branding and branding.get("colors"):
        colors = ", ".join([c.get("hex", "") for c in branding["colors"]])
    title = (ebook_meta or {}).get("title") or (branding or {}).get("title") or "Digital Product"
    concept = (branding or {}).get("cover_concept", "")
    return (
        f"A premium, professional ebook cover illustration (NO text, NO words, NO letters). "
        f"Concept: {concept}. Theme relates to: {title}. "
        f"Use this color palette: {colors}. Clean, modern, high-end editorial style, abstract or symbolic imagery, "
        f"balanced composition, suitable as a book cover background. Vertical portrait orientation."
    )
