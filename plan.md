# Khova AI — Development Plan (V1)

## 1) Objectives
- Deliver a **full-stack AI Digital Product Factory** (not a chatbot) that turns minimal user input into **market-researched, market-validated opportunities** and then into **real digital assets**: **PDF eBook**, **XLSX spreadsheet**, **responsive website**.
- Guarantee **product quality** via: real cited research, transformation-driven structure, format-specific creation (not copy/paste), QA with scoring + fix suggestions, consistent branding/design system.
- Support **multi-provider LLMs** (OpenAI/Anthropic/Gemini) and **multi-language** (UI language separate from product language; default Indonesian).
- Implement **deferred Google auth** (only when generating/saving), plus dev-login bypass for tests.

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation): prove the 5 hard primitives  ✅ DONE (all 5 passed)
> Result: (a) LLM JSON ok; (b) Gemini googleSearch returned 11 real citations (note: grounding URLs are vertexaisearch redirect links + real source titles); (c) Nano Banana returns image (mime can be image/jpeg -> handle dynamically); (d) WeasyPrint PDF+embedded image ok; (e) openpyxl multi-sheet+formula ok.

**User stories**
1. As a builder, I want one script that proves LLM JSON output works so the pipeline can pass structured data reliably.
2. As a builder, I want real web search with citations so opportunities are evidence-based.
3. As a builder, I want Nano Banana images saved to PNG so covers/illustrations are real assets.
4. As a builder, I want PDF generation with embedded images so eBooks are truly exportable.
5. As a builder, I want XLSX generation with multiple sheets + formulas so spreadsheet products are real.

**Steps**
- Create `/app/backend/poc_core.py` that sequentially validates:
  - (a) LlmChat structured JSON generation (choose provider/model from config).
  - (b) Gemini `googleSearch` grounding (or Anthropic `web_search`) returning **title+url citations**.
  - (c) Nano Banana image generation (`gemini-3.1-flash-image-preview`) → base64 → save PNG.
  - (d) WeasyPrint HTML/CSS → PDF embedding the generated PNG (base64 image).
  - (e) openpyxl workbook: 2+ sheets, styled header row, at least one formula (e.g., SUM).
- Add minimal utilities: safe logging (no base64 dumps), deterministic output paths under `/app/backend/generated/poc/`.
- If provider web search is unavailable on chosen model, auto-fallback to the other provider; if none available, mark research as unavailable and output HYPOTHESIS/ASSUMPTION placeholders (no fake citations).
- Iterate until **all 5 outputs are produced** and validated by file existence + non-trivial byte size.

### Phase 2 STATUS: Backend + Frontend COMPLETE. All endpoints validated via curl (research 23 citations, 20 scored opps, positioning, transformation, spreadsheet->real XLSX, website->real HTML, ebook plan+section+intro+cover->real 977KB PDF, QA, branding, dev-login). Frontend: premium landing, 10-step wizard, all step screens, dashboard/projects/settings, deferred login modal, sample project. NEXT: comprehensive testing agent run.

### Phase 2 STATUS: COMPLETE ✅ (V1 shipped). Testing agent: 21/22 passed; fixed login-modal auto-close + pending-action resume (stale ensureAuth closure -> now uses stable userRef), verified working. Backend all endpoints validated. Frontend full pipeline wired.
### DEV NOTE: /api/auth/dev-login bypass present for testing — REMOVE before production.

### Phase 2 — V1 App Development (core workflow end-to-end, auth deferred)
**User stories**
1. As a user with only a vague idea, I want to continue without filling everything so I can start fast.
2. As a user, I want opportunities backed by real sources so I trust what I’m building.
3. As a user, I want to choose eBook/XLSX/Website and get a real downloadable product.
4. As a user, I want progress saved after each step so I can return later.
5. As a user, I want QA feedback and improvements without losing the original version.

**Backend (FastAPI + MongoDB)**
- Data models/collections (MVP but complete): `users`, `user_sessions`, `projects`, `assets`.
  - `projects` embeds: discover_input, research_bundle (sources+findings), opportunities[], selected_opportunity, positioning, transformation, format_choice, ebook (plan+sections+versions), spreadsheet (spec+sheet_defs), website (spec+html), qa_reports[], branding, exports.
- Provider abstraction:
  - Settings: provider + model per agent category (cheap vs strong) stored per project (with defaults).
  - Implement `llm_call_json()` helper enforcing JSON schema; `llm_call_text()` for prose.
- Agent endpoints (structured, incremental, cache-first):
  - `POST /api/projects` create draft project.
  - `POST /api/projects/{id}/discover` save input.
  - `POST /api/projects/{id}/research` run provider-hosted web search; store sources+findings with labels (RESEARCH-BACKED/HYPOTHESIS/ASSUMPTION).
  - `POST /api/projects/{id}/opportunities` generate ~20 from stored research; include scoring + overall score.
  - `POST /api/projects/{id}/select-opportunity`.
  - `POST /api/projects/{id}/positioning`.
  - `POST /api/projects/{id}/transformation` + store palette.
  - `POST /api/projects/{id}/format`.
  - `POST /api/projects/{id}/create/ebook` (planner → section generation jobs → visuals plan → image gen → manuscript sections).
  - `POST /api/projects/{id}/create/spreadsheet` (spec → sheet_defs → build XLSX via openpyxl).
  - `POST /api/projects/{id}/create/website` (spec → generate HTML/CSS → store + serve).
  - `POST /api/projects/{id}/qa` (scores + issues + recommended fixes; apply fixes creates new version).
  - `POST /api/projects/{id}/branding`.
  - `POST /api/projects/{id}/export/ebook` (WeasyPrint PDF using design system + embed visuals).
  - `GET /api/projects/{id}/download/{asset_id}`.
  - `GET /api/sites/{project_id}` serve generated website.
- Job/progress:
  - Lightweight `generation_jobs` inside project: step, status, progress counters, error, retry.
- File handling:
  - Save generated assets under `/app/backend/generated/{project_id}/...` and register in `assets` with mime/type/path.
  - Optional uploads: store file metadata + extracted text (if supported); never claim facts came from uploads.

**Frontend (React + shadcn/ui + Tailwind)**
- Premium SaaS layout: Landing (commercial) → Dashboard/Projects/Settings.
- Creation stepper: Discover → Research → Opportunities → Positioning → Transformation → Format → Create → QA → Branding → Export.
- Multi-language:
  - UI language toggle (id/en) via i18n dictionary.
  - Product language selector stored in project; every generation request includes product_language.
- Deferred auth UX:
  - Allow anonymous exploration up to Opportunities.
  - On actions that persist/generate/export: show modal “Sign in to generate/save” → redirect to Emergent OAuth.
- Core screens:
  - Research view shows sources table (title, url) + findings with labels.
  - Opportunities cards with scoring, sorting/filtering/compare; “Build this opportunity”.
  - Editor panels for Positioning + Transformation (fully editable).
  - Format chooser with Coming Soon cards.
  - Create views:
    - eBook: outline + section progress + preview (HTML) + cover preview.
    - Spreadsheet: sheet list + spec preview + “Generate XLSX”.
    - Website: live preview iframe and copy editor per section.
  - Export: PDF preview + download, XLSX download, website link.

### Phase 3 — Auth + hardening + acceptance test completion
**User stories**
1. As a user, I want to sign in only when necessary so I don’t bounce early.
2. As a signed-in user, I want my projects private and accessible across sessions.
3. As a user, I want retries on failed generations so I don’t lose work.
4. As a user, I want version history for edits/QA improvements.
5. As a user, I want consistent visuals across cover/pages so the product looks premium.

**Steps**
- Implement Emergent Google Auth:
  - Frontend redirect with dynamic `window.location.origin`.
  - AuthCallback exchange `session_id` → backend `/api/auth/session` sets cookie.
  - `/api/auth/me`, `/api/auth/logout`.
- Add dev-login bypass endpoint for testing only; document in `/app/memory/test_credentials.md`.
- Authorization enforcement:
  - Anonymous allowed read-only of draft until generate/save; enforce owner checks on project endpoints.
- Design consistency check for eBook design system and export.
- Seed a sample project (lightweight) to demonstrate UI flow without expensive generation.
- Run full end-to-end acceptance test; fix only failing components; avoid unnecessary regeneration.

## 3) Next Actions
1. Implement and run `/app/backend/poc_core.py` until all 5 primitives pass (PNG/PDF/XLSX created).
2. Define minimal JSON schemas for: research_bundle, opportunity, positioning, transformation, ebook_plan, ebook_section, spreadsheet_spec, website_spec, qa_report.
3. Build backend project endpoints + asset storage around the proven primitives.
4. Build React stepper UI + project persistence + previews/downloads.
5. Add deferred Google Auth + dev-login bypass; run e2e acceptance testing and patch gaps.

## 4) Success Criteria
- **POC passes**: produces valid JSON, cited research, PNG image, PDF with embedded image, XLSX with formula.
- **Pipeline works end-to-end** with minimal input: Discover → Research (with citations stored) → ~20 scored opportunities → select → positioning → transformation + palette → choose format → generate eBook/XLSX/Website → QA report → branding → export.
- **Real assets**: downloadable PDF, downloadable XLSX, and a working responsive website served from an endpoint.
- **Quality controls**: research conclusions labeled, QA scores + fixes, design system enforced.
- **No lost progress**: project state persists after every major step; retries don’t wipe previous versions.
- **Multi-language respected**: product language consistently applied across all generated content.
