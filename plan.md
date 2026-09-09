# Khova AI — Refinement Phase 1–2 Plan (Core UX + Localization + Design System + eBook Quality + PDF + Productization)

## 1) Objectives

### Phase 1 Goals (✅ completed)
- Enforce **two separate language concepts** end-to-end:
  - **UI Language** (navigation/labels/status/errors)
  - **Product / Asset Language** (generated ebook/spreadsheet/website + exporter “chrome” strings)
- Upgrade Dashboard into an **AI workspace** centered on “What do you want to create?” with **minimal input** and progressive optional context.
- Improve workflow clarity:
  - Expandable Opportunity details (no truncation dead-ends)
  - Scoring explanations (non-cluttered)
  - Research sources + claim labels remain visible and honest
  - Single canonical palette used everywhere + editable in one place
  - Actionable feedback/toasts + better ebook preview “paper” look
  - QA Apply Improvement clearly updates content + preview + preserves versions
- **Visual Design System re-theme** (premium blue Khova identity):
  - Align global UI tokens/typography/gradients with **existing Khova blue logo**
  - Support **light + dark mode tokens** (tokens implemented; toggle can be added later)
  - Improve hierarchy/whitespace/readability while preserving existing functionality and components

### Phase 2 Goals (✅ completed)
Focus areas: eBook generation quality, visuals, cover, PDF quality, math notation, productization, real bonuses.

- **eBook structure upgraded** (not just “long text”):
  - Strong product structure: cover → colophon → TOC → intro → chapters with worked examples + exercises + summaries → action-plan closing chapter → bonus materials
  - “Toolkit feel”: actionable blocks (action steps, checklists, answer guidance), not just prose
- **Visual design and editorial hierarchy** in PDF:
  - Improved typography hierarchy, whitespace, chapter openers, varied block styles
  - Canonical palette consistently used (no random colors)
- **Chapter illustrations**:
  - A visual planning layer in the ebook plan; 2–4 purposeful visuals with type/aspect/placement
  - Embedded inside the relevant chapter
- **Cover quality**:
  - AI generates **artwork only** (no text)
  - Deterministic HTML overlays for title/subtitle/author/brand
  - **PDF Page 1 is the cover** (no metadata page before cover)
- **PDF rendering QA**:
  - Manual visual QA performed on a real 60-page educational ebook
  - Fixed a real rendering bug (fractions breaking due to `inline-flex` in WeasyPrint)
- **Mathematical notation**:
  - Safe HTML-based math rules (sup/sub/fractions/sqrt/unicode symbols); never LaTeX
  - Fractions now render reliably after `inline-block` fix
- **Productization + bonuses become real assets**:
  - Bonuses can be generated as **real downloadable XLSX** tools (with example rows + formulas)

### Current Objective (post Phase 2)
- Maintain stability and prevent regression with lightweight, repeatable smoke checks.
- Add **repeatable QA automation** for PDF rendering (visual regression) and math rendering coverage.
- Keep Phase 3+ scoped to refinement only unless explicitly requested (no billing/quota, no public publishing/hosting, no major AI cost infra).

---

## 2) Implementation Steps (Phases)

### Phase 1 — Core UX / Localization / Design System (✅ completed)
(Kept as historical record; implemented and verified.)

1) Exporter language localization
- `exporters.py` `LABELS` dict keyed by language (id/en + additional es/fr/de/pt/ja)
- Thread `product_language` through `build_ebook_html` + `build_website_html`
- Update `server.py` callsites
- Replace hardcoded Indonesian exporter “chrome” strings

2) Ebook preview portrait look (`@media screen` paper-like pages)
- Add screen-only portrait “paper” styling without altering PDF print rules
- Regression fix: do not override cover background

3) Dashboard AI-input-first workspace
- Minimal input allowed
- Optional context accordion

4) Opportunities: full detail dialog + scoring help dialog

5) Canonical palette: single source of truth, editable and reused everywhere

6) Workflow feedback improvements + QA apply improvements visible

7) Global visual re-theme: premium Khova-blue UI tokens + typography

**Status:** ✅ complete; verified via screenshots + `testing_agent_v3` (iteration_2).

---

### Phase 2 — eBook Generation, Visual Design, PDF Quality & Productization (✅ completed)

#### A) eBook planner upgrades (backend)
1) **Ebook plan structure upgrade** (`agents.py`)
- `generate_ebook_plan` now outputs:
  - `meta.is_math_heavy` flag
  - `toc[]` includes: `needs_worked_example`, `needs_exercise`, and mandatory final `kind="action_plan"` chapter
  - `visuals[]`: 2–4 purposeful visuals with `visual_type`, `prompt`, `aspect_ratio`, `placement`
  - `bonuses[]`: expanded enum (diagnostic_test, mistake_log, checklist, tracker, planner, progress_tracker, reference_sheet, answer_sheet, decision_tree, template, etc.)

**Status:** ✅ implemented and validated with a real educational project.

#### B) Section-level generation quality (backend)
2) **Instructional chapter writing** (`agents.py`)
- `generate_ebook_section` now enforces:
  - Worked example blocks when appropriate
  - Exercise blocks including **answer guidance**
  - A dedicated action-plan closing chapter prompt

3) **Math notation safety** (`agents.py`)
- Added `MATH_NOTATION_RULES`:
  - No LaTeX / no `$...$`
  - Use safe HTML: `sup/sub`, `.frac`, `.sqrt`, unicode symbols
- `rewrite_section` now receives `is_math` flag from `server.py` callsites

**Status:** ✅ implemented and validated.

#### C) Bonus generator becomes real assets (backend)
4) **Bonus asset spec generator** (`agents.py`)
- New `generate_bonus_asset_spec()` produces a spreadsheet-shaped JSON tool with:
  - 1–2 sheets
  - usable template/example rows
  - formulas + dropdowns when relevant

5) **Bonus XLSX generation endpoint** (`server.py`)
- New endpoint: `POST /projects/{id}/ebook/bonus/{index}/generate`
- Generates and registers a downloadable XLSX asset via `exporters.build_xlsx`
- Uses **canonical palette**

**Status:** ✅ implemented and validated (real XLSX with formulas).

#### D) PDF template + cover redesign (backend)
6) **Exporter overhaul** (`exporters.py`)
- Designed cover:
  - Full-bleed cover artwork image (AI artwork only)
  - Dark gradient scrim
  - Deterministic HTML typography overlay (title/subtitle/author)
  - Page 1 is cover
- Editorial chapter openers:
  - chapter kicker + large ghost number + title + dek line
- Varied block styles (reduced “colored box repetition”):
  - callout, pullquote, example, exercise, answer-guide, action-steps, summary
- Rendering robustness:
  - `orphans/widows`
  - `page-break-inside: avoid` for tables and content blocks
  - improved image framing (`object-fit: contain`)

7) **Critical bug fix found during visual QA**
- Fractions used `display:inline-flex` → WeasyPrint broke fraction layout (orphan operators, split numerator/denominator)
- Fixed to reliable `inline-block` approach

**Status:** ✅ fixed and verified with a live re-render.

#### E) Frontend wiring (existing UI preserved)
8) `EbookCreator.js` enhancements
- Bonus generate + download buttons
- Bulk “generate all illustrations” action
- Action-plan chapter badge

**Status:** ✅ implemented.

#### F) Phase 2 completion test (✅ completed)
Representative educational product end-to-end test:
- Created a real math-heavy ebook (“The Algebra Tutor at Home”)
- Generated plan + 8 chapters + intro
- Generated cover artwork + exported PDF
- Rasterized 60 pages with `pdftoppm` and visually inspected ~15 pages
- Verified:
  - Cover page 1
  - TOC/intro/chapter openers
  - Worked examples + exercises + summaries + action-plan closing chapter
  - 4 purposeful illustrations embedded in chapters
  - Math notation (fractions/exponents/equations) correct after fix
  - No orphan numbers, clipping, overlapping, broken tables, blank pages in sampled inspection
  - Canonical palette consistency + product_language consistency (English)
  - Bonuses generated as real usable XLSX assets with formulas

---

### Phase 3 — Testing & Validation (updated post Phase 2)

#### A) Regression hardening (recommended)
1) Add repeatable smoke scripts (new)
- `/app/backend/poc_localization_exporters.py`:
  - Assert exporter chrome strings match `product_language`
- `/app/backend/poc_pdf_math_render.py`:
  - Generate a small ebook section containing fractions/exponents/sqrt/sub/sup and export PDF
  - Rasterize key pages with `pdftoppm`
  - Store images for manual review (and future pixel-diff if desired)
- `/app/backend/poc_bonus_xlsx.py` (recommended):
  - Generate at least one bonus XLSX and validate that formulas exist in expected cells

2) Add a lightweight manual QA checklist doc
- Cover on page 1
- TOC page
- One chapter opener
- One worked example
- One exercise + answer guide
- One illustration placement
- One multi-fraction equation
- Bonus XLSX download and basic formula validation

#### B) Automated/agent testing
3) Run `testing_agent_v3` end-to-end regression
- dashboard → discover → research → opportunities → positioning → transformation → format → create → QA → branding → export
- deferred auth still intact
- localization consistency
- theme consistency

**Status:** ✅ completed (iteration_3) with one reported P0 that was a **false positive**.

##### Note on `iteration_3` “P0: /projects redirects to homepage”
- Root cause: **correct access control**, not a routing bug.
  - A project owned by user A correctly cannot be opened under user B’s session (403/redirect).
- Verified by:
  1) Opening `/projects` successfully under a consistent session
  2) Opening a project **owned by the current user** and confirming the Phase 2 Create UI renders
  3) Live-clicking **“Buat File Bonus”** and observing it complete with toast + download button
- **No code changes needed.**

---

## 3) Next Actions

1) Add Phase 2-specific POC scripts
- `poc_pdf_math_render.py` (math rendering + PDF rasterization check)
- `poc_bonus_xlsx.py` (bonus XLSX generation + formula presence validation)

2) Expand math coverage stress tests
- roots (supported), plus additional symbols and edge cases:
  - limits/integrals/summations (unicode-based)
  - long equations near page breaks

3) Optional UI hardening (still refinement-scope)
- Surface illustration plan list in UI (chapter → purpose → type) for review before generating images
- Add “Download bonus assets” section in Export step (aggregated)

---

## 4) Success Criteria

### Phase 1 (✅)
- No random UI/product language mixing; exporter chrome strings follow Product Language (✅)
- Dashboard minimal-input first (✅)
- Opportunities fully inspectable + scoring help (✅)
- Honest research labels + sources (✅)
- One canonical palette editable + propagates (✅)
- Ebook preview portrait pages on screen; cover readable (✅)
- QA apply updates content + persists + versions (✅)
- Blue premium UI design system; logo untouched (✅)

### Phase 2 (✅)
- eBook structure reads like a **real product/toolkit**, not filler (✅)
- PDF cover is **page 1** with deterministic typography overlay (✅)
- Purposeful illustrations embedded in chapters (✅)
- PDF rendering visually QA’d; no major layout defects in sampled inspection (✅)
- Math notation renders correctly (fractions/exponents verified; LaTeX avoided) (✅)
- Bonuses produce **real downloadable assets** (XLSX) with usable structure and formulas (✅)
- Canonical palette consistently used across cover/chapter blocks/bonus styling where applicable (✅)

### Phase 3 (⏳ recommended hardening)
- Add repeatable QA automation/smoke scripts for PDF + math
- Add repeatable bonus-XLSX validation script
- Optional: dark-mode toggle UI wiring (tokens already exist)
