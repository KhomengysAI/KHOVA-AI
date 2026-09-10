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
import io
import uuid
import zipfile
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# This harness runs the app in-process via ASGITransport (no real network
# origin involved), so it isn't the cross-origin-deployment scenario SEC-04's
# CORS_ORIGINS fail-fast check guards against. Opt in explicitly rather than
# letting `import server` below raise for an unset CORS_ORIGINS.
os.environ.setdefault("KHOVA_ALLOW_WILDCARD_CORS", "true")

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


async def _mock_research(discover, lang, mc):
    return {"status": "complete", "findings": [{"label": "HYPOTHESIS", "text": "x"}],
            "sources": [{"title": "s", "url": "http://x"}], "summary": "sum"}


async def _mock_opps(discover, research, lang, mc):
    return [{"id": f"op_{i}", "name": f"Opp {i}", "scores": {}, "overall_score": 7} for i in range(3)]


async def _mock_positioning(opp, discover, lang, mc):
    return {"one_liner": "x", "target_customer": "y"}


async def _mock_transformation(opp, positioning, lang, mc):
    return {"core_transformation": "x", "categories": []}


def install_mocks():
    agents.generate_website_spec = _mock_website_spec
    agents.regenerate_website_section = _mock_website_section
    agents.qa_review = _mock_qa_review
    agents.rewrite_section = _mock_rewrite
    agents.run_market_research = _mock_research
    agents.generate_opportunities = _mock_opps
    agents.generate_positioning = _mock_positioning
    agents.generate_transformation = _mock_transformation


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

        # ================= FINAL HARDENING PHASE TESTS =================
        import ratelimit
        from db import GENERATED_DIR

        # ---- Anonymous AI rate limiting (Priority 1) ----
        # Deterministic limits for the test (limits() reads env live).
        os.environ["KHOVA_ANON_MAX_AI"] = "3"
        os.environ["KHOVA_ANON_MIN_INTERVAL_SEC"] = "0"
        os.environ["KHOVA_ANON_DEDUP_SEC"] = "0"
        os.environ["KHOVA_ANON_COOLDOWN_SEC"] = "60"
        os.environ["KHOVA_ANON_WINDOW_SEC"] = "3600"
        # This in-process test harness sends X-Forwarded-For itself to simulate
        # distinct client IPs (there's no real socket peer via ASGITransport),
        # i.e. it plays the role of a trusted reverse proxy — so opt in to
        # trusting that header for the duration of this test (see REL-01:
        # ratelimit.client_ip() no longer trusts X-Forwarded-For by default).
        os.environ["KHOVA_TRUST_PROXY_HEADERS"] = "true"

        anon_proj = (await c.post("/api/projects", json={"title": "Anon"})).json()
        apid = anon_proj["id"]; project_ids.append(apid)
        ip1 = {"X-Forwarded-For": "203.0.113.10"}
        statuses = [(await c.post(f"/api/projects/{apid}/research", headers=ip1)).status_code for _ in range(5)]
        check("anon: first 3 AI requests allowed", statuses[:3] == [200, 200, 200])
        check("anon: request past the limit blocked (429)", statuses[3] == 429)
        blk = await c.post(f"/api/projects/{apid}/research", headers=ip1)
        check("anon: cooldown keeps blocking (429)", blk.status_code == 429)
        _d = blk.json().get("detail")
        _msg = _d.get("message") if isinstance(_d, dict) else str(_d)
        check("anon: block message tells user to sign in", "sign in" in _msg.lower())
        check("anon: exactly 3 usage records recorded server-side",
              (await db.anon_ai_usage.count_documents({"ip": "203.0.113.10"})) == 3)

        # authenticated user is NOT subject to the anon limit (uses entitlements)
        auth_statuses = [(await c.post(f"/api/projects/{apid}/research", headers={**uh, "X-Forwarded-For": "203.0.113.10"})).status_code for _ in range(5)]
        check("authenticated user bypasses anon limit entirely", all(s == 200 for s in auth_statuses))

        # duplicate / simultaneous flood guard (fresh IP)
        os.environ["KHOVA_ANON_DEDUP_SEC"] = "30"; os.environ["KHOVA_ANON_MAX_AI"] = "50"
        ip2 = {"X-Forwarded-For": "203.0.113.20"}
        ap2 = (await c.post("/api/projects", json={"title": "Anon2"})).json()["id"]; project_ids.append(ap2)
        d1 = await c.post(f"/api/projects/{ap2}/research", headers=ip2)
        d2 = await c.post(f"/api/projects/{ap2}/research", headers=ip2)
        check("anon: duplicate/simultaneous request blocked", d1.status_code == 200 and d2.status_code == 429)

        # rapid-fire guard (fresh IP)
        os.environ["KHOVA_ANON_DEDUP_SEC"] = "0"; os.environ["KHOVA_ANON_MIN_INTERVAL_SEC"] = "5"
        ip3 = {"X-Forwarded-For": "203.0.113.30"}
        ap3 = (await c.post("/api/projects", json={"title": "Anon3"})).json()["id"]; project_ids.append(ap3)
        f1 = await c.post(f"/api/projects/{ap3}/research", headers=ip3)
        f2 = await c.post(f"/api/projects/{ap3}/research", headers=ip3)
        check("anon: rapid-fire request blocked (too_fast)", f1.status_code == 200 and f2.status_code == 429)
        # reset limits to defaults for the remainder
        os.environ["KHOVA_ANON_MIN_INTERVAL_SEC"] = "0"; os.environ["KHOVA_ANON_MAX_AI"] = "8"
        for ip in ("203.0.113.10", "203.0.113.20", "203.0.113.30"):
            await db.anon_ai_usage.delete_many({"ip": ip}); await db.anon_blocks.delete_many({"ip": ip})

        # ---- Product bundle download (Priority 3) ----
        bpid = f"prj_bundle_{uuid.uuid4().hex[:8]}"; project_ids.append(bpid)
        bdir = GENERATED_DIR / bpid; bdir.mkdir(parents=True, exist_ok=True)
        (bdir / "book.pdf").write_bytes(b"%PDF-1.4 fake ebook")
        (bdir / "bonus1.xlsx").write_bytes(b"XLSX-BONUS-1")
        (bdir / "bonus2.xlsx").write_bytes(b"XLSX-BONUS-2")
        MIME_X = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        bassets = [
            {"id": "a1", "type": "pdf", "key": "ebook_pdf", "filename": "book.pdf", "mime": "application/pdf", "path": str(bdir / "book.pdf"), "size": 19},
            {"id": "a2", "type": "bonus", "key": "bonus_0", "filename": "tracker.xlsx", "mime": MIME_X, "path": str(bdir / "bonus1.xlsx"), "size": 12},
            {"id": "a3", "type": "bonus", "key": "bonus_1", "filename": "tracker.xlsx", "mime": MIME_X, "path": str(bdir / "bonus2.xlsx"), "size": 12},
            {"id": "a4", "type": "pdf", "key": "missing", "filename": "missing.pdf", "mime": "application/pdf", "path": str(bdir / "nope.pdf"), "size": 0},
        ]
        await db.projects.insert_one({"id": bpid, "user_id": uid, "title": "Bundle Book", "assets": bassets,
                                      "created_at": billing.now_iso(), "updated_at": billing.now_iso()})
        bresp = await c.get(f"/api/projects/{bpid}/bundle", headers=uh)
        check("bundle: 200 + application/zip", bresp.status_code == 200 and bresp.headers.get("content-type") == "application/zip")
        zf = zipfile.ZipFile(io.BytesIO(bresp.content))
        znames = zf.namelist()
        check("bundle: PDF included at root", "book.pdf" in znames)
        check("bundle: bonus XLSX included under bonuses/", sum(1 for n in znames if n.startswith("bonuses/")) == 2)
        check("bundle: duplicate filenames de-collided", len(set(znames)) == len(znames))
        check("bundle: missing file skipped gracefully (3 files)", "missing.pdf" not in znames and len(znames) == 3)
        check("bundle: zip contents are real bytes", zf.read("book.pdf") == b"%PDF-1.4 fake ebook")

        oemail = f"other_{uuid.uuid4().hex[:6]}@example.com"
        oh = await login(c, oemail, "Other")
        oid = (await db.users.find_one({"email": oemail}))["user_id"]; user_ids.append(oid)
        unauth = await c.get(f"/api/projects/{bpid}/bundle", headers=oh)
        check("bundle: another user is blocked (403)", unauth.status_code == 403)

        epid2 = f"prj_empty_{uuid.uuid4().hex[:8]}"; project_ids.append(epid2)
        await db.projects.insert_one({"id": epid2, "user_id": uid, "title": "Empty", "assets": [],
                                      "created_at": billing.now_iso(), "updated_at": billing.now_iso()})
        emptyresp = await c.get(f"/api/projects/{epid2}/bundle", headers=uh)
        check("bundle: no downloadable assets -> 400", emptyresp.status_code == 400)

        # ---- Website theme (deterministic, no AI) (Priority 5) ----
        st = await c.patch(f"/api/projects/{pid}/website/style", headers=uh, json={"style": "Editorial"})
        check("website theme change 200 (deterministic)", st.status_code == 200)
        webnow = st.json()["website"]
        check("website theme persisted", webnow.get("style") == "Editorial")
        check("website theme rebuilds draft preview", bool(webnow.get("draft_html")))
        check("website theme keeps canonical palette", "#0B6E6B" in (webnow.get("draft_html") or ""))
        bad = await c.patch(f"/api/projects/{pid}/website/style", headers=uh, json={"style": "Rainbow"})
        check("website theme: invalid preset rejected (400)", bad.status_code == 400)
        # all 5 presets render deterministically with palette preserved
        import exporters as _exp
        _spec = webnow.get("spec")
        _pal = {"primary": "#0B6E6B"}
        check("website: all 5 presets render + palette canonical",
              all("#0B6E6B" in _exp.build_website_html(_spec, _pal, s, "id") for s in ["Minimal", "Modern", "Premium", "Editorial", "Bold"]))

        # ---- Usage insights (own data only) (Priority 6) ----
        usremail = f"usage_{uuid.uuid4().hex[:6]}@example.com"
        ush = await login(c, usremail, "UsageUser")
        usrid = (await db.users.find_one({"email": usremail}))["user_id"]; user_ids.append(usrid)
        up1 = f"prj_usage_{uuid.uuid4().hex[:6]}"; up2 = f"prj_usage_{uuid.uuid4().hex[:6]}"; project_ids += [up1, up2]
        await db.projects.insert_one({"id": up1, "user_id": usrid, "title": "Usage A", "format": "ebook", "assets": [], "created_at": billing.now_iso(), "updated_at": billing.now_iso()})
        await db.projects.insert_one({"id": up2, "user_id": usrid, "title": "Usage B", "format": "website", "assets": [], "created_at": billing.now_iso(), "updated_at": billing.now_iso()})

        async def _mkjob(u, p, charged):
            await db.generation_jobs.insert_one({"id": f"job_{uuid.uuid4().hex[:10]}", "user_id": u, "project_id": p,
                                                 "task": "ebook_section", "status": "completed", "credits_charged": charged,
                                                 "created_at": billing.now_iso()})
        await _mkjob(usrid, up1, 2); await _mkjob(usrid, up1, 2); await _mkjob(usrid, up2, 3)
        await _mkjob(oid, up1, 99)  # another user's job on the same project MUST NOT leak
        usage = (await c.get("/api/me/usage", headers=ush)).json()
        check("usage: total credits used = own only (7)", usage["total_credits_used"] == 7)
        check("usage: product_generations counts own products (2)", usage["product_generations"] == 2)
        _per = {p["project_id"]: p for p in usage["products"]}
        check("usage: per-product A credits = 4", _per.get(up1, {}).get("credits_used") == 4)
        check("usage: per-product B credits = 3", _per.get(up2, {}).get("credits_used") == 3)
        check("usage: other user's 99 credits not leaked", all(x["credits_used"] != 99 for x in usage["products"]))
        # scoping: another user cannot see this user's usage
        other_usage = (await c.get("/api/me/usage", headers=oh)).json()
        check("usage: scoped per-user (other user sees own only)", up1 not in {p["project_id"] for p in other_usage["products"]} or other_usage["total_credits_used"] == 99)

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

    # ---- refund on charged-then-failed job (Priority 4) ----
    await db.users.update_one({"user_id": tuid}, {"$set": {"credits": 20}})
    fake_job = {"id": f"job_{uuid.uuid4().hex[:10]}", "user_id": tuid, "task": "ebook_section",
                "credits_charged": 5, "status": "completed"}
    await db.generation_jobs.insert_one(dict(fake_job))
    refunded = await jobs.fail(fake_job, "boom")
    check("refund: charged job refunds its credits", refunded == 5)
    check("refund: balance restored (+5 => 25)", (await billing.get_balance(tuid)) == 25)
    check("refund: job flagged credits_refunded / zeroed charge",
          fake_job.get("credits_refunded") == 5 and fake_job.get("credits_charged") == 0)
    # a failure that never charged must not refund (no false refund)
    fake_job2 = {"id": f"job_{uuid.uuid4().hex[:10]}", "user_id": tuid, "task": "positioning",
                 "credits_charged": 0, "status": "running"}
    await db.generation_jobs.insert_one(dict(fake_job2))
    refunded2 = await jobs.fail(fake_job2, "boom")
    check("refund: no-charge failure refunds 0 (no false refund)",
          refunded2 == 0 and (await billing.get_balance(tuid)) == 25)

    await cleanup(user_ids, project_ids)

    print(f"\n==== RESULT: {PASS} passed, {FAIL} failed ====")
    if FAILURES:
        print("Failed:", ", ".join(FAILURES))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
