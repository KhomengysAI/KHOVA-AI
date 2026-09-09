# Khova AI — Phase 3 + 4: Production Architecture, Economy, QA, Website, Hardening

## Context / What already exists (verified by code inspection)
- FARM stack. Phases 1 & 2 complete (localization scaffold, AI-first dashboard, design system, PDF/math, XLSX bonuses).
- **Google Auth already implemented** (Emergent managed): `AuthContext.googleLogin` → `auth.emergentagent.com` → `AuthCallback` → `POST /api/auth/session`. Dev-login also present.
- Generation endpoints exist for ebook / spreadsheet / website / qa / branding / bonuses.
- `models_config` is user-controlled (to be removed from UX; kept internal).

## Decisions (locked)
- Respond to user in **English**.
- Preserve premium Khova-blue design system (no new theme; reuse existing tokens/components).
- Do NOT regenerate expensive AI products for testing — use code-level + mocked tests.
- Internal model routing; users never pick provider/model.

---

## PHASE A — Fixes & Quick Wins (Status: COMPLETED)
1. **Language fix** (`agents.py`): deterministic per-product-language block headings (example / exercise / answer-guide / action-steps / summary / key-idea). Removes mixed EN/ID labels. (DONE)
2. **Remove AI Preferences UI** (`Settings.js`): delete "AI Model per Agent" card + `/config/models` usage. Keep backend routing internal. (DONE)
3. **Dark Mode**: `ThemeContext` + toggle in Settings + quick toggle in AppShell (tokens already exist). (DONE)

## PHASE B — Backend Economy & Cost Architecture (Status: COMPLETED)
4. `billing.py`: PLANS (free/creator/pro, configurable), entitlements, atomic credit ledger, usage log, `ensure_user_economy`. (DONE)
5. `redeem.py` (in billing): admin redeem-code create + user redeem (validate expiry / limit / already-redeemed / single-use). (DONE)
6. `jobs.py`: generation job lifecycle (QUEUED/RUNNING/COMPLETED/FAILED/CANCELLED), dedup/idempotency, retry limits, deterministic caching helpers. (DONE)
7. `model_router.py`: task → tier (low/mid/high) → provider/model; usage estimate; never exposed to users. (DONE)
8. `auth.py`: role (user/admin via ADMIN_EMAILS), economy backfill on login. (DONE)
9. Wire into `server.py`: server-side entitlement + credit check (reserve→deduct on success, no charge on fail), job tracking, `/api/me/economy`, `/api/redeem`, `/api/admin/*`. (DONE)

## PHASE C — Website Product System (Status: COMPLETED)
10. DRAFT / PREVIEW / PUBLISHED states; publish/unpublish; regenerate single section; edit+save; stable public URL (`/api/sites/{slug}` serves PUBLISHED snapshot, draft preserved). Frontend WebsiteCreator upgrade. (DONE)

## PHASE D — QA Apply-Improvement (section-level) (Status: COMPLETED)
11. QA issues get stable ids + target section; `POST /qa/apply-issue/{issue_id}` applies ONE targeted improvement to the affected section only, persists, marks issue resolved, keeps version history, updates preview. Frontend per-issue Apply. (DONE)

## PHASE E — Frontend Hardening (Status: COMPLETED)
12. Credits + plan badge (AppShell); Redeem code section (Settings); Admin page `/admin` (users/plans/credits/codes/jobs/usage). (DONE)
13. Clear action feedback (what happened / credits deducted / remaining). (DONE)

## PHASE F — Lightweight Testing (mocked) (Status: COMPLETED)
14. Backend pytest: entitlements, credit atomicity/protection, redeem validation, roles, QA apply logic, localization labels, model routing, job state transitions, retry protection, website publish states — all with mocked AI. (DONE)

## PHASE G — Final Report (Status: COMPLETED)

---

## Success Criteria
- Normal user cannot find AI Preferences anywhere. (A2)
- Product language consistent (no mixed EN/ID block labels). (A1)
- Dark mode toggle works and persists. (A3)
- Credits/entitlements enforced server-side; frontend cannot manipulate. (B)
- Redeem codes validated server-side with all edge cases. (B5)
- Website has DRAFT/PREVIEW/PUBLISHED; publish gives shareable URL; draft preserved. (C)
- QA "Apply Improvement" actually edits only the affected section + persists + marks resolved. (D)
- Lightweight tests pass without expensive AI generation. (F)
