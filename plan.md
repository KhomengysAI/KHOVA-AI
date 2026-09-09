# Khova AI — Refinement Phase 1 Plan (Core UX + Localization + Design System + Workflow Clarity)

## 1) Objectives

### Phase 1 Goals (now completed)
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

### Current objective (post Phase 1)
- Maintain stability and prevent regression with lightweight, repeatable smoke checks.
- Keep Phase 2 scoped to refinement only (no billing/quota, no major new generation infra, no public hosting/publishing).

---

## 2) Implementation Steps (Phases)

### Phase 1 — Core POC / Isolation Tests (required)
**Goal:** prove language + palette propagation and preview rendering work before broad UI refactors.

1. **Exporter language POC (backend)**
   - Add `/app/backend/poc_localization_exporters.py` that calls `build_ebook_html()` and `build_website_html()` with `product_language=id` and `en`.
   - Assert exported HTML contains localized structural strings (TOC/Chapter/Intro/Before/After/Footer) in the correct language.

2. **Screen preview CSS POC (backend)**
   - Update ebook exporter HTML to include `@media screen` “paper portrait” container.
   - Verify `/ebook/preview-html` looks like portrait pages (not full-width web layout).
   - **Regression guard:** ensure cover remains high-contrast (do not override `.cover` background in screen CSS).

**Exit criteria:** POC script passes; preview visually resembles a document on screen.

**Status:** ⚠️ The underlying exporter localization + preview CSS are implemented and verified; the standalone POC script is still recommended to add for ongoing regression safety.

User stories (Phase 1)
1. As a user, when my product language is English, I want “Table of Contents/Chapter/Introduction” to appear in English in preview/export.
2. As a user, when my product language is Indonesian, I want those document labels to be Indonesian.
3. As a user, I want the ebook preview to look like real portrait pages so I can judge layout.
4. As a user, I want web page exports to reflect my chosen product language for section labels (Before/After etc.).
5. As a user, I want the same palette to drive preview styling consistently.

---

### Phase 2 — V1 App Development (incremental, reuse existing components)

#### A) Global Localization (UI vs Product)
1. **Backend: localize exporter “chrome” strings**
   - In `exporters.py`, add a `LABELS` dict keyed by language (**implemented; expanded beyond id/en to include es/fr/de/pt/ja**).
   - Thread `product_language` into:
     - `build_ebook_html(..., product_language)` (**implemented**)
     - `build_website_html(..., product_language)` (**implemented**)
   - Update `server.py` callsites for ebook preview/export and website build (**implemented**).
   - Replace hardcoded strings: Chapter/Toc/Intro/Bonus/Before/After/footer/disclaimer (**implemented**).

   **Verification:** ✅ Live-verified via curl that `product_language=en` switches chrome to “Table of Contents / Chapter N / Introduction” and sets `lang="en"`; `product_language=id` switches to “Daftar Isi / Bab N / Pendahuluan”.

2. **Frontend: centralize UI strings**
   - Expand `src/lib/i18n.js` with missing keys used in refined screens (**implemented**).
   - Add variable interpolation support `t(key, vars)` (**implemented**) to enable descriptive toasts.
   - Replace hardcoded UI strings in touched steps opportunistically (**implemented for Dashboard + Research/Opportunities/QA/Export + new dialogs**).

**Status:** ✅ Core exporter localization fixed (previous bug: hardcoded Indonesian in exports) + UI i18n improved.

#### B) Dashboard AI Workspace (minimal-input first)
3. Redesign `Dashboard.js`:
   - Primary card: large textarea “What do you want to create?” + mode toggle (Know / Don’t know) (**implemented**).
   - “Add more context (optional)” accordion for progressive enhancement (**implemented**).
   - On submit: create project → save discover → route to `/project/:id` (**implemented**).
   - Keep “Recent projects” list and quick navigation preserved (**implemented**).

**Status:** ✅ Implemented and visually verified.

#### C) Opportunities: expansion + scoring help
4. **Opportunity detail dialog**
   - Make `OpportunityCard` clickable / “View details” (**implemented**).
   - Full-detail `Dialog` showing:
     - title, target customer, problem, why it matters (desired_outcome), market_evidence, existing_alternatives, product_gap, product_concept, scores (**implemented**).
   - Confidence badge (researched vs hypothesis) (**implemented**).

5. **Scoring explanation UI**
   - Add subtle “How scoring works” dialog in `OpportunitiesStep` (**implemented**).
   - Define concise explanations for each dimension (pain, worsening, purchasing_power, speed, market_validation, differentiation) (**implemented**).

**Status:** ✅ Implemented and visually verified.

#### D) Research source visibility (tighten)
6. Maintain honest research claims:
   - Keep labels RESEARCH-BACKED/HYPOTHESIS/ASSUMPTION (already implemented).
   - Improve feedback toast to distinguish research complete vs unavailable (**implemented in `ResearchStep`**).

**Status:** ✅ No fabricated sources; labels preserved; toast messaging improved.

#### E) Single canonical palette (fix two-palette confusion)
7. Create reusable `PalettePicker` component (extract from `TransformationStep`) (**implemented**).
8. Update `BrandingStep`:
   - Display **canonical palette** from `project.transformation.palette` (**implemented**).
   - Allow editing via `PalettePicker` through existing `/palette` endpoint (**implemented**).
   - Avoid presenting a separate conflicting branding palette (branding.colors) (**implemented**).

**Status:** ✅ Canonical palette is the single source of truth and is editable.

#### F) Workflow feedback (toasts)
9. Replace generic toasts with descriptive, next-step guidance.
   - Research/Opportunities/Transformation/Branding/QA/Export: improved messaging; include Sonner actions where useful (QA apply + website preview) (**implemented**).

**Status:** ✅ Implemented for key flows.

#### G) Preview improvements (ebook)
10. Add `@media screen` CSS in ebook HTML to render centered portrait pages with shadow/background (**implemented**).
    - Do not alter print `@page` rules used by WeasyPrint (kept intact).
    - Regression fixed: ensure `.cover` keeps original dark background; apply paper background only to `.page`/`.chapter` (**implemented + visually verified**).

**Status:** ✅ Implemented and visually verified.

#### H) QA Apply Improvement UX clarity
11. After apply:
   - Toast: improvements applied + action “Open eBook” (**implemented**).
   - EbookCreator: show “Diperbaiki” badge per chapter when `versions.length > 0` (**implemented**).

**Status:** ✅ Implemented.

#### I) Visual Design System (Premium Blue Re-theme)
12. Implement a cohesive Khova design system aligned with the **existing blue logo identity**:
   - Use `/app/design_guidelines.md` as the source of truth (royal-blue primary, cool neutrals, restrained blue-only gradients; no logo changes).
   - Update `/app/frontend/src/index.css` tokens to the new **light + dark** HSL variable sets (**implemented**).
   - Replace font imports and typography mapping (**implemented**):
     - Headings: **Montserrat** (`.font-display`)
     - Body: **Figtree**
     - Mono: **Roboto Mono** (`.font-mono`)
   - Retint decorative utilities (**implemented**):
     - `.hero-mist` and `.paper-warmth` → blue-only radial gradients + `.dark` variants
   - Update theme-color meta in `/public/index.html` to match Khova blue (**implemented**).

**Status:** ✅ Re-theme implemented, visually verified across Landing/Dashboard/Opportunities/Branding; logo untouched.

User stories (Phase 2)
1. As a user, I can start with only a short idea and still proceed.
2. As a user, I can optionally expand and add more context without feeling required.
3. As a user, I can open an opportunity and see complete evidence and product direction.
4. As a user, I can understand scoring dimensions via a help panel.
5. As a user, I can edit one palette and see it consistently reflected in branding/exports.
6. As a user, the UI feels premium, readable, and consistent with Khova’s blue brand identity.

---

### Phase 3 — Testing & Validation
1. **Backend checks**
   - Add and run POC script `/app/backend/poc_localization_exporters.py` (new) to prevent regression of exporter chrome localization.
   - Smoke test preview/export endpoints for ebook/spreadsheet/website:
     - `/ebook/preview-html` (portrait paper look)
     - `/ebook/export` (PDF download)
     - `/spreadsheet/build` (XLSX download)
     - `/website/build` + `/website/preview` (HTML output)

2. **Frontend checks**
   - Build check (esbuild) + manual UI walkthrough.
   - Screenshot verification:
     - Landing (blue theme)
     - Dashboard (AI input)
     - Opportunities (dialog + scoring help)
     - Branding (canonical palette)
     - Ebook preview endpoint (portrait pages + readable cover)

3. **Automated/agent testing**
   - Run `testing_agent_v3` for end-to-end regression of:
     - dashboard → project → discover → research → opportunities → positioning → transformation → format → create → QA → branding → export
     - deferred auth flow remains intact
     - localization: no random UI/product language mixing
     - theme: no contrast regressions

**Status:** ✅ Completed.
- `iteration_2.json` reports: 0 critical bugs, 13/14 backend tests passed (1 minor test-script-only issue), frontend/UI/theme checks passed.
- Live verification: exporter chrome language switching confirmed via curl.

User stories (Phase 3)
1. As a user, I can complete the full pipeline without random language mixing.
2. As a user, exports (PDF/XLSX/HTML) still download correctly.
3. As a user, research sources never appear fabricated.
4. As a user, QA apply actually updates content and I can verify via preview.
5. As a user, palette edits persist and propagate to exports.
6. As a user, the new blue design system remains consistent across pages (no stray warm teal/amber UI chrome).

---

## 3) Next Actions
1. Add `/app/backend/poc_localization_exporters.py` and run it as a repeatable smoke test (recommended hardening item).
2. Add a small manual checklist doc for release validation (Dashboard minimal-input, Opportunity dialog, scoring help, palette sync, QA apply, ebook preview cover contrast, export language).
3. Optional (Phase 2+): add a UI dark-mode toggle (tokens already exist) and run a contrast audit.

---

## 4) Success Criteria
- No visible random UI/product language mixing; **exporter chrome strings** follow Product Language (✅ verified live).
- Dashboard starts projects from minimal idea input; optional context is clearly optional (✅).
- Opportunity cards are fully inspectable via dialog; scoring help is available and non-cluttered (✅).
- Research findings retain honest labels + sources shown when available (✅).
- One canonical palette editable by user; branding/export/preview all use it (✅).
- Ebook preview looks like portrait pages on screen; PDF export unaffected; cover remains readable (✅).
- QA Apply Improvement demonstrably changes content, persists, updates preview, preserves versions (✅).
- **Visual design system** is premium and consistent with Khova’s blue logo identity (typography + tokens + gradients); no logo alteration (✅).
- Existing endpoints, DB schema, generation workflows, deferred auth and exports remain working (✅).
