"""Phase 3+4 lightweight architecture tests for Khova AI.

Runs the REAL FastAPI app in-process via httpx ASGITransport with ALL expensive
AI calls monkeypatched (no credits spent, no network). Validates:
  - entitlements / plan view
  - credit atomicity + no-negative protection
  - redeem code validation (happy path + every edge case)
  - roles (admin gating)
  - free-tier creation limit
  - generation-job state transitions (begin/complete/fail)
  - duplicate + retry protection
  - internal model routing
  - localization block labels
  - website DRAFT/PREVIEW/PUBLISHED + publish/unpublish + section regen
  - QA apply-issue (section-level, marks only the intended issue resolved)

Run:  python tests/test_phase34.py
"""
import os
import sys
import uuid
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

import agents
import billing
import jobs
import model_router
from db import db
import server

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}")


# --- Mock all expensive AI so no credits/network are used --------------------
async def _mock_website_spec(*a, **k):
    return {"brand": "Test", "hero": {"headline": "H", "subheadline": "S", "cta": "Go"},
            "problem": {"title": "P", "body": "b", "bullets": ["x"]},
            "benefits": {"title": "B", "items": [{"title": "t", "desc": "d"}]},
            "faq": {"title": "FAQ", "items": [{"q": "q", "a": "a"}]},
            "final_cta": {"headline": "CTA", "cta": "Buy"}}


async def _mock_website_section(spec, section, instruction, lang, mc):
    return {"headline": "NEW HEADLINE", "subheadline": "new", "cta": "Go"}


async def _mock_qa_review(fmt, content, transformation, lang, mc):
    return {
        "scores": {"clarity": 7, "logic": 7, "usefulness": 7, "originality": 7,
                   "formatting": 7, "transformation_alignment": 7, "language_consistency": 6},
        "overall": 7,
        "issues": [
            {"type": "language_inconsistency", "severity": "high", "detail": "English label in ID text",
             "fix": "translate", "chapter_num": 1, "location": "Summary"},
            {"type": "repetition", "severity": "low", "detail": "repeats", "fix": "trim", "chapter_num": 0, "location": "intro"},
        ],
        "recommended_improvements": ["tighten"],
    }


async def _mock_rewrite(existing_html, instruction, lang, mc, is_math=False):
    return existing_html + "<!-- rewritten -->"


def install_mocks():
    agents.generate_website_spec = _mock_website_spec
    agents.regenerate_website_section = _mock_website_section
    agents.qa_review = _mock_qa_review
    agents.rewrite_section = _mock_rewrite


async def login(client, email, name):
    r = await client.post("/api/auth/dev-login", json={"email": email, "name": name})
    tok = r.json()["session_token"]
    return {"Authorization": f"Bearer {tok}"}


async def insert_pipeline_project(user_id, fmt="website", counted=False):
    """Insert a fully-pipelined project directly (skips the expensive discover->transform AI)."""
    pid = f"prj_test_{uuid.uuid4().hex[:8]}"
    opp = {"id": "op_1", "name": "Test Opp", "scores": {}, "overall_score": 8}
    doc = {
        "id": pid, "user_id": user_id, "title": "Test", "status": "creating",
        "current_step": "create", "ui_language": "id", "product_language": "id",
        "discover": {}, "research": {"status": "complete"},
        "opportunities": [opp], "selected_opportunity_id": "op_1",
        "positioning": {"one_liner": "x"}, "transformation": {"core_transformation": "x", "palette": {"primary": "#0B6E6B"}},
        "format": fmt, "ebook": None, "spreadsheet": None, "website": None, "qa": [],
        "branding": None, "assets": [], "counted_as_creation": counted,
        "created_at": billing.now_iso(), "updated_at": billing.now_iso(),
    }
    await db.projects.insert_one(dict(doc))
    return pid


async def insert_ebook_project(user_id):
    pid = f"prj_test_{uuid.uuid4().hex[:8]}"
    ebook = {
        "meta": {"title": "T", "is_math_heavy": False}, "toc": [{"chapter_num": 1, "title": "C1"}],
        "sections": [{"chapter_num": 1, "title": "C1", "content_html": "<p>original</p>"}],
        "introduction_html": "<p>intro</p>", "visuals": [], "bonuses": [], "illustrations": {},
        "design_system": {}, "progress": {"done": 1, "total": 1},
    }
    doc = {
        "id": pid, "user_id": user_id, "title": "Ebook", "status": "creating", "current_step": "qa",
        "ui_language": "id", "product_language": "id", "discover": {}, "research": {"status": "complete"},
        "opportunities": [{"id": "op_1"}], "selected_opportunity_id": "op_1",
        "positioning": {"x": 1}, "transformation": {"core_transformation": "x"},
        "format": "ebook", "ebook": ebook, "qa": [], "assets": [], "counted_as_creation": True,
        "created_at": billing.now_iso(), "updated_at": billing.now_iso(),
    }
    await db.projects.insert_one(dict(doc))
    return pid


async def cleanup(user_ids, project_ids):
    # Never delete the owner's real accounts (admin@khova.ai / tester@khova.ai).
    protected = set()
    for email in ("admin@khova.ai", "tester@khova.ai"):
        u = await db.users.find_one({"email": email}, {"user_id": 1})
        if u:
            protected.add(u["user_id"])
    for uid in user_ids:
        if uid in protected:
            continue
        await db.users.delete_many({"user_id": uid})
        await db.credit_ledger.delete_many({"user_id": uid})
        await db.generation_jobs.delete_many({"user_id": uid})
        await db.redemptions_log.delete_many({"user_id": uid})
    for pid in project_ids:
        await db.projects.delete_many({"id": pid})


async def main():
    install_mocks()
    server.generate_image = lambda *a, **k: asyncio.sleep(0, result=(b"IMG", "image/png"))

    transport = httpx.ASGITransport(app=server.app)
    user_ids, project_ids = [], []
    uemail = f"tuser_{uuid.uuid4().hex[:6]}@example.com"
    aemail = "admin@khova.ai"

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        uh = await login(c, uemail, "TUser")
        ah = await login(c, aemail, "Admin")

        # ---- economy view ----
        eco = (await c.get("/api/me/economy", headers=uh)).json()
        check("free plan default", eco["plan"] == "free")
        check("free start credits = 100", eco["credits"] == 100)
        check("free creations_remaining = 3", eco["creations_remaining"] == 3)
        check("website_publish locked on free", eco["features"]["website_publish"] is False)
        uid = (await db.users.find_one({"email": uemail}))["user_id"]
        aid = (await db.users.find_one({"email": aemail}))["user_id"]
        user_ids += [uid, aid]

        # ---- roles ----
        check("normal user 403 on admin", (await c.get("/api/admin/overview", headers=uh)).status_code == 403)
        ov = await c.get("/api/admin/overview", headers=ah)
        check("admin overview 200", ov.status_code == 200)

        # ---- redeem code lifecycle ----
        mk = await c.post("/api/admin/codes", headers=ah,
                          json={"plan": "creator", "credits": 100, "max_redemptions": 1, "expires_days": 5, "prefix": "TEST"})
        code = mk.json()["code"]
        check("invalid code rejected", (await c.post("/api/redeem", headers=uh, json={"code": "TEST-NOPE-NOPE"})).status_code == 400)
        rr = await c.post("/api/redeem", headers=uh, json={"code": code})
        check("valid redeem ok", rr.status_code == 200 and rr.json()["credits_granted"] == 100)
        eco2 = (await c.get("/api/me/economy", headers=uh)).json()
        check("plan upgraded to creator", eco2["plan"] == "creator")
        check("credits added (200)", eco2["credits"] == 200)
        check("creator has unlimited creations", eco2["creations_remaining"] is None)
        again = await c.post("/api/redeem", headers=uh, json={"code": code})
        check("re-redeem blocked (already/ exhausted)", again.status_code == 400)

        # expired code
        ek = await c.post("/api/admin/codes", headers=ah, json={"plan": None, "credits": 10, "max_redemptions": 5, "expires_days": -1, "prefix": "EXP"})
        echeck = await c.post("/api/redeem", headers=uh, json={"code": ek.json()["code"]})
        check("expired code rejected", echeck.status_code == 400)

        # ---- website DRAFT/PREVIEW/PUBLISHED ----
        pid = await insert_pipeline_project(uid, "website")
        project_ids.append(pid)
        r = await c.post(f"/api/projects/{pid}/website/spec", headers=uh, json={"style": "Modern"})
        check("website spec draft created", r.status_code == 200 and r.json()["website"]["status"] == "draft")
        # publish (creator can publish)
        pub = await c.post(f"/api/projects/{pid}/website/publish", headers=uh)
        check("website publish ok (creator)", pub.status_code == 200 and pub.json()["website"]["status"] == "published")
        check("public_url returned", "public_url" in pub.json())
        # public serving
        pubhtml = await c.get(f"/api/sites/{pid}")
        check("published site served publicly", pubhtml.status_code == 200 and "html" in pubhtml.text.lower())
        # edit draft after publish -> draft changes, published snapshot preserved
        spec = pub.json()["website"]["spec"]
        spec["hero"]["headline"] = "EDITED DRAFT"
        await c.patch(f"/api/projects/{pid}/website/spec", headers=uh, json={"spec": spec})
        served_after_edit = (await c.get(f"/api/sites/{pid}")).text
        check("publish snapshot preserved after draft edit", "EDITED DRAFT" not in served_after_edit)
        # section regenerate (draft only)
        rs = await c.post(f"/api/projects/{pid}/website/section/regenerate", headers=uh, json={"section": "hero"})
        check("section regenerate updates draft", rs.status_code == 200 and rs.json()["website"]["spec"]["hero"]["headline"] == "NEW HEADLINE")
        check("regen sets status back to draft", rs.json()["website"]["status"] == "draft")
        # unpublish
        unp = await c.post(f"/api/projects/{pid}/website/unpublish", headers=uh)
        check("unpublish ok", unp.status_code == 200)
        check("unpublished site 404 public", (await c.get(f"/api/sites/{pid}")).status_code == 404)
        check("preview still served for owner", (await c.get(f"/api/sites/{pid}?preview=1")).status_code == 200)

        # ---- website publish gating on FREE plan ----
        femail = f"free_{uuid.uuid4().hex[:6]}@example.com"
        fh = await login(c, femail, "Free")
        fid = (await db.users.find_one({"email": femail}))["user_id"]
        user_ids.append(fid)
        fpid = await insert_pipeline_project(fid, "website")
        project_ids.append(fpid)
        await c.post(f"/api/projects/{fpid}/website/spec", headers=fh, json={"style": "Modern"})
        fpub = await c.post(f"/api/projects/{fpid}/website/publish", headers=fh)
        check("free plan publish blocked (403)", fpub.status_code == 403)

        # ---- QA apply-issue (section-level) ----
        epid = await insert_ebook_project(uid)
        project_ids.append(epid)
        qa = await c.post(f"/api/projects/{epid}/qa", headers=uh, json={})
        check("qa run ok", qa.status_code == 200)
        report = qa.json()["qa"][0]
        check("qa issues have ids", all(i.get("id") for i in report["issues"]))
        check("qa issues start unresolved", all(i["resolved"] is False for i in report["issues"]))
        target = report["issues"][0]  # chapter 1
        ap = await c.post(f"/api/projects/{epid}/qa/apply-issue/{target['id']}", headers=uh)
        check("apply-issue ok", ap.status_code == 200)
        proj_after = ap.json()
        sec_html = proj_after["ebook"]["sections"][0]["content_html"]
        check("targeted chapter content modified", "rewritten" in sec_html)
        check("prior version kept", len(proj_after["ebook"]["sections"][0].get("versions", [])) == 1)
        issues_after = proj_after["qa"][0]["issues"]
        check("only targeted issue resolved", issues_after[0]["resolved"] is True and issues_after[1]["resolved"] is False)
        check("intro untouched (other issue not applied)", proj_after["ebook"]["introduction_html"] == "<p>intro</p>")

    # ---- direct module tests: credits / jobs / limits ----
    print("\n[module-level economy/jobs]")
    tuid = f"user_mod_{uuid.uuid4().hex[:8]}"
    user_ids.append(tuid)
    await db.users.insert_one({"user_id": tuid, "email": f"{tuid}@x.com", "plan": "free",
                               "credits": 5, "creations_used": 0, "role": "user"})
    # atomic deduct
    bal = await billing.deduct_credits(tuid, 3, "test")
    check("deduct leaves 2", bal == 2)
    # over-deduct blocked (no negative)
    try:
        await billing.deduct_credits(tuid, 10, "test")
        check("over-deduct raises", False)
    except ValueError:
        check("over-deduct raises (no negative balance)", True)
    check("balance still 2 after failed deduct", (await billing.get_balance(tuid)) == 2)
    # ledger recorded
    check("ledger entries recorded", (await db.credit_ledger.count_documents({"user_id": tuid})) >= 1)

    # model routing
    check("router: ebook_section -> high tier", model_router.route("ebook_section")["tier"] == "high")
    check("router: branding -> low tier", model_router.route("branding")["tier"] == "low")
    check("router: cover -> image model", model_router.route("cover")["category"] == "image")

    # localization labels present & distinct
    check("section labels id != en", agents._section_labels("id")["summary"] != agents._section_labels("en")["summary"])
    check("id summary is Ringkasan", agents._section_labels("id")["summary"] == "Ringkasan")

    # jobs begin/complete deducts + creation counting
    u = await db.users.find_one({"user_id": tuid})
    u["credits"] = 10; u["plan"] = "free"; u["creations_used"] = 0
    await db.users.update_one({"user_id": tuid}, {"$set": {"credits": 10, "creations_used": 0}})
    u = await db.users.find_one({"user_id": tuid})
    proj = {"id": f"prj_mod_{uuid.uuid4().hex[:6]}", "user_id": tuid, "counted_as_creation": False}
    job = await jobs.begin(u, proj, "ebook_plan")
    check("job begins RUNNING", job["status"] == "running")
    info = await jobs.complete(u, proj, job)
    check("ebook_plan charged 2 credits", info["cost"] == 2 and info["balance"] == 8)
    check("creation counted", info["counted_creation"] is True)
    jrec = await db.generation_jobs.find_one({"id": job["id"]})
    check("job marked COMPLETED", jrec["status"] == "completed")

    # duplicate protection
    job2 = await jobs.begin(u, proj, "positioning")
    try:
        await jobs.begin(u, proj, "positioning")
        check("duplicate job blocked", False)
    except jobs.DuplicateJob:
        check("duplicate concurrent job blocked", True)
    await jobs.fail(job2, "test")

    # creation limit on free after 3 creations
    await db.users.update_one({"user_id": tuid}, {"$set": {"creations_used": 3, "plan": "free"}})
    u = await db.users.find_one({"user_id": tuid})
    proj2 = {"id": f"prj_mod_{uuid.uuid4().hex[:6]}", "user_id": tuid, "counted_as_creation": False}
    try:
        await jobs.begin(u, proj2, "spreadsheet_spec")
        check("free creation limit enforced", False)
    except jobs.CreationLimitReached:
        check("free creation limit enforced", True)

    # insufficient credits raises in begin
    await db.users.update_one({"user_id": tuid}, {"$set": {"credits": 0, "creations_used": 0, "plan": "creator"}})
    u = await db.users.find_one({"user_id": tuid})
    proj3 = {"id": f"prj_mod_{uuid.uuid4().hex[:6]}", "user_id": tuid, "counted_as_creation": True}
    try:
        await jobs.begin(u, proj3, "ebook_section")
        check("insufficient credits blocks begin", False)
    except jobs.InsufficientCredits:
        check("insufficient credits blocks begin", True)

    await cleanup(user_ids, project_ids)

    print(f"\n==== RESULT: {PASS} passed, {FAIL} failed ====")
    if FAILURES:
        print("Failed:", ", ".join(FAILURES))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
