# **Khova AI**

## **Table of Contents**

1. [Short Description](#i-short-description)
2. [Tech Stack & Hosting](#ii-tech-stack--hosting)
3. [Repository Structure](#iii-repository-structure)
4. [The Product Pipeline & User Workflow](#iv-the-product-pipeline--user-workflow)
5. [Application Processing Pipeline](#v-application-processing-pipeline)
6. [Database Schema](#vi-database-schema)
7. [Self-Hosting & Migration Status](#vii-self-hosting--migration-status)
8. [FAQ](#viii-faq)
9. [Third-Party Services & Legal Notes](#ix-third-party-services--legal-notes)

---

## **I. Short Description**

Khova AI is an AI-powered **digital product factory**, not a chatbot. It takes a user's idea, expertise, interests, or a vague sense of "I want to make something," and walks it through a fixed pipeline — market research → opportunity discovery → positioning → an emotional "transformation map" → format selection → generation → QA → branding → export — until it produces a real, downloadable digital product: an eBook (PDF), a spreadsheet (XLSX), or a simple published website.

The same discovered opportunity is meant to be reusable across formats: the market research, positioning, and transformation-map stages happen once, and the user only picks a product format afterward. A set of specialized backend "agents" (`backend/agents.py`) each own one stage of that pipeline — a market researcher, an opportunity generator, a positioning/transformation strategist, per-format creators (eBook, spreadsheet, website), a QA reviewer, and a branding generator — rather than one prompt regenerating the whole product on every change.

Two product-safety principles run through the whole app:

- **Research before invention.** Before the app proposes product opportunities, it must run real-time web research (via provider-hosted search grounding) and label every conclusion as `RESEARCH-BACKED`, `HYPOTHESIS`, or `ASSUMPTION`. If web research isn't available, the app is required to say so rather than pretend it browsed the internet.
- **Deferred authentication.** The discovery funnel — Discover → Research → Opportunities → Positioning → Transformation → Format — works fully anonymously (rate-limited server-side by IP; see [Section V](#v-application-processing-pipeline)) so a visitor can explore before creating an account. An account is only required once the user commits to actually generating a product (eBook chapters, a spreadsheet, or a website) or wants to export/download it.

Khova AI also runs its own internal **credit and plan economy** (Free / Creator / Pro): the frontend never chooses which AI provider or model runs a task, and it never decides what a user is entitled to — every entitlement check and every credit deduction happens server-side (`backend/billing.py`, `backend/jobs.py`), atomically, so a balance can't go negative and a generation can't be double-charged.

The default UI and product language is Indonesian; both are independently configurable per project (see [Section IV](#iv-the-product-pipeline--user-workflow)).

---

## **II. Tech Stack & Hosting**

| Layer | Choice | Why |
| --- | --- | --- |
| **Backend framework** | [FastAPI](https://fastapi.tiangolo.com/) (`backend/server.py`) | Async-native Python framework so the app can `await` long-running AI generation calls (research, writing, image generation) without blocking the process. |
| **ASGI server** | [Uvicorn](https://www.uvicorn.org/) | Reference ASGI server FastAPI runs under. |
| **Database** | [MongoDB](https://www.mongodb.com/) via [Motor](https://motor.readthedocs.io/) (`backend/db.py`) | Async Mongo driver. Chosen (over a relational DB) because a `project` document is a deeply nested, evolving tree (discover → research → opportunities → positioning → transformation → format-specific content → QA → branding → assets) that's naturally a single document rather than a strict multi-table join. See [Section VI](#vi-database-schema). |
| **AI orchestration** | `emergentintegrations` (`LlmChat`) wrapping OpenAI, Google Gemini, and Anthropic | A single provider-abstraction client used by every AI call in the app, so `backend/llm_service.py` can route different task categories to different providers/models without every agent needing its own SDK integration. **This package and the key it authenticates with are Emergent-platform-specific — see [Section VII](#vii-self-hosting--migration-status) for what that means for self-hosting.** |
| **Internal model router** | `backend/model_router.py` | Users never pick a provider or model. Every AI task is classified into a complexity tier (`low` / `mid` / `high`) and routed to a fixed provider+model pair per tier — cheap/fast models for classification and formatting, stronger models for research synthesis, long-form writing, and QA. Image tasks (`cover`, `illustration`) always route to the configured image model. |
| **PDF export** | [WeasyPrint](https://weasyprint.org/) (`backend/exporters.py`) | Renders the generated eBook's HTML/CSS straight to a real PDF, including an embedded base64 cover/illustration. Needs its system-level dependencies (Cairo, Pango, GDK-PixBuf) present on the host — these are not pure-Python and are easy to miss outside a prebuilt container image. |
| **Spreadsheet export** | [openpyxl](https://openpyxl.readthedocs.io/) | Builds real, multi-sheet `.xlsx` files (with formulas) from the spreadsheet spec an agent generates. |
| **Auth (current)** | Emergent's hosted Google-auth broker, with a `dev-login` bypass for testing (`backend/auth.py`, `frontend/src/context/AuthContext.js`) | See [Section VII](#vii-self-hosting--migration-status) — this is the other Emergent-specific dependency and the main blocker to fully self-hosting today. |
| **Billing / entitlements** | Custom server-side credit ledger + plan definitions (`backend/billing.py`) | No third-party billing provider is wired up yet — `stripe` is listed in `requirements.txt` but isn't called anywhere in `billing.py`. Plans, feature flags, and credit costs per AI task are defined in code, not hardcoded into the frontend. |
| **Rate limiting (anonymous)** | Custom Mongo-backed sliding window, keyed by client IP (`backend/ratelimit.py`) | Protects the free, unauthenticated discovery funnel from abuse — a real cost/abuse surface since it runs actual AI calls with no login and no credit charge. Fully configurable via environment variables (see [Section V](#v-application-processing-pipeline)). |
| **Frontend framework** | [React 19](https://react.dev/) via [Create React App](https://create-react-app.dev/) + [CRACO](https://craco.js.org/) (`frontend/`) | Standard CRA app with CRACO for build-config overrides (dev-server compatibility shims, an optional Emergent visual-editing dev tool — see [Section VII](#vii-self-hosting--migration-status)). |
| **UI components** | [shadcn/ui](https://ui.shadcn.com/) on [Radix UI](https://www.radix-ui.com/) primitives + [Tailwind CSS](https://tailwindcss.com/) | Accessible unstyled primitives (dialogs, dropdowns, tabs, tooltips, etc.) styled with Tailwind utility classes, matching the `components.json` shadcn config in the repo. |
| **Routing** | [React Router](https://reactrouter.com/) | Client-side routing across the landing page, dashboard, project wizard steps, settings, and admin pages (`frontend/src/pages/`). |
| **Data fetching / forms** | `axios`, `@tanstack/react-query`, `swr`, `react-hook-form` + `zod` | REST calls to the FastAPI backend, server-state caching, and schema-validated forms. |
| **Motion / charts** | `framer-motion`, `recharts` | Wizard/step transitions and the admin usage/credit charts. |

**Hosting.** The project was originally built and run on [Emergent](https://emergent.sh/) (`fastapi_react_mongo_shadcn_base_image_cloud_arm` base image — see `.emergent/emergent.yml`), which provided the container image, the Google-auth broker, and the metered LLM key described in [Section VII](#vii-self-hosting--migration-status). This fork's goal is to run the same FastAPI + React + MongoDB stack outside that platform. There is no `Dockerfile`/`docker-compose.yml` in the repository yet — Emergent built the container from its own base-image spec — so a self-hoster needs to supply their own deployment config (e.g. a Dockerfile per service, or separate FastAPI/React/MongoDB hosts) in addition to resolving the auth and LLM blockers in Section VII.

---

## **III. Repository Structure**

```text
backend/
   server.py              FastAPI app, all HTTP routes, CORS, startup/shutdown
   auth.py                Emergent session exchange, dev-login bypass, session cookies
   db.py                  Motor/MongoDB client, generated-asset directory, doc serialization
   billing.py             Plans, credit ledger, feature entitlements, redeem codes
   jobs.py                Generation-job lifecycle (reserve credits -> run -> charge/refund)
   model_router.py        Task -> complexity tier -> provider/model routing (never user-facing)
   llm_service.py         emergentintegrations LlmChat wrapper: llm_json/llm_text/research/generate_image
   ratelimit.py           IP-keyed sliding-window rate limiter for the anonymous funnel
   agents.py              One function per pipeline stage (research, opportunities, positioning,
                           transformation, ebook plan/section, spreadsheet spec, website spec, QA,
                           branding, bonus assets, cover-prompt builder)
   exporters.py           Deterministic (non-AI) renderers: ebook HTML->PDF, XLSX builder,
                           website HTML builder + style presets, per-language export labels
   sample_data.py         Builds a lightweight demo project (no expensive AI assets) for /projects/sample
   poc_core.py             Standalone script validating the app's five hard external dependencies
                           (LLM JSON gen, web-search-grounded research, image gen, PDF export, XLSX
                           export) — run manually, not imported by the running server
   generated/              AI-generated asset output (PDFs, XLSX, PNGs, HTML) — not source
   requirements.txt        Python runtime dependencies
   tests/, pytest.ini      Backend test suite (pytest-xdist, 2 fixed workers)

frontend/
   craco.config.js         CRA build overrides + dev-server compatibility shims
   tailwind.config.js, components.json   Tailwind + shadcn/ui configuration
   src/
      pages/                Landing, Dashboard, Projects, NewProduct, Settings, Admin, Wizard,
                             AuthCallback
      pages/steps/           One component per wizard step: Discover, Research, Opportunities,
                             Positioning, Transformation, Format, Create (per-format creators:
                             Ebook/Spreadsheet/Website), QA, Branding, Export
      context/               AuthContext (session state, Emergent login redirect), ThemeContext
      components/ui/         shadcn/ui component library
      lib/                   API client (reads REACT_APP_BACKEND_URL), shared utilities
      hooks/, constants/      Shared hooks and test-id constants

tests/                    Root-level test package
test_reports/              Iteration test-run artifacts from prior development rounds
plan.md, design_guidelines.md, auth_testing.md, test_result.md
                            Working/planning notes carried over from earlier development rounds
.emergent/                 Emergent platform bootstrap/orchestration metadata (base image tag,
                            restore markers, cron/webhook scripts). Not read by the application
                            code at all — safe to delete or .gitignore for a self-hosted fork.
```

---

## **IV. The Product Pipeline & User Workflow**

### A. The ten pipeline stages

Every product moves through the same fixed sequence, tracked on the project document as `current_step`:

1. **Discover** — the user answers "What do you want to create?" in one of two modes: *"I Know What I Want To Build"* (free-text idea, plus optional expertise/audience/interests/uploaded reference material) or *"I Don't Know Yet"* (the app generates candidate directions from whatever context is provided, down to none at all). No field is required to proceed.
2. **Research** — real-time, provider-hosted web research on the user's topic/niche/audience (existing products, pricing, complaints, unmet needs, competitor positioning), with every source's title, URL, and relevance retained.
3. **Opportunities** — market-validated "profitable pockets" generated from the research, each scored and labeled by evidence strength.
4. **Positioning** — a specific product angle/positioning statement for the opportunity the user selects.
5. **Transformation** — a "visceral transformation map": the target reader's emotional state, core fear, daily experience, identity, practical situation, and desired outcome — the emotional throughline the eventual product content is written around.
6. **Format** — the user picks the product format (**eBook/PDF**, **Spreadsheet/XLSX**, or **Simple Website** are fully implemented; Video, Image/Visual, Social Content, Templates, Workbook, Checklist, Prompt Pack, and Toolkit are the spec's extensible secondary formats) — deliberately *after* the opportunity and transformation are already defined, so the same opportunity can be re-run into a different format later.
7. **Create** — the format-specific creator agent generates the actual content: eBook chapters (with optional AI cover and per-chapter illustrations), an XLSX spec (sheets, columns, formulas, example data), or a website spec (sections, copy, one of five visual style presets: Minimal, Modern, Premium, Editorial, Bold).
8. **QA** — a QA agent reviews the generated content and can auto-apply fixes, either to the whole product or to one flagged issue at a time.
9. **Branding** — name, tagline, and visual-identity text generated for the finished product, feeding the eBook cover prompt.
10. **Export** — deterministic (non-AI) rendering to the final downloadable asset(s): eBook → PDF via WeasyPrint, spreadsheet → XLSX via openpyxl, website → static HTML (publishable to a stable public URL). A one-click "Download Bundle" zips every generated asset for a project together.

### B. Deferred authentication

Stages 1–6 (Discover through Format) work fully anonymously — a visitor can run the entire discovery funnel without an account, subject to the IP-based rate limiter in [Section V](#v-application-processing-pipeline). An account is required starting at stage 7 (actually generating eBook/spreadsheet/website content), and for exporting, publishing, or downloading anything. Creating a project itself, viewing it, and patching its discovery/research/opportunity/positioning/transformation/format fields are all allowed without login; every AI call from stage 7 onward requires `get_current_user` (a valid session).

### C. Plans & credits

Every AI generation task has a fixed credit cost (`backend/billing.py`); the discovery-funnel tasks (research, opportunities, positioning, transformation) always cost `0` credits — they're intentionally free so a user can explore before spending anything. Three plans gate both feature access and per-plan limits:

| Plan | Starting credits | Free full-product creations | Website publishing | Advanced QA | Research depth |
| --- | --- | --- | --- | --- | --- |
| **Free** | 100 | 3 (lifetime) | ✗ | ✗ | Basic |
| **Creator** | 1,000 | Unlimited (subject to credits) | ✓ | ✓ | Standard |
| **Pro** | 5,000 | Unlimited (subject to credits) | ✓ | ✓ | Deep |

A user's plan can be upgraded, and credits topped up, via server-generated **redeem codes** (`backend/billing.py`'s `create_redeem_code`/`redeem_code`) — admin-only to create, single- or multi-use, with optional expiry. Accounts whose email is listed in `KHOVA_ADMIN_EMAILS` get the `admin` role and bypass entitlement/credit checks entirely (still logged for monitoring).

### D. Running it locally

#### Main Branch
```bash
git clone https://github.com/KhomengysAI/KHOVA-AI.git
cd KHOVA-AI
```
#### This Fork
```bash
git clone https://github.com/Akirenaki/KHOVA-AI.git
cd KHOVA-AI
```
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # see Section VII for the emergentintegrations/litellm caveats
uvicorn server:app --reload
```

```bash
# Frontend (separate terminal)
cd ../frontend
yarn install    # or npm install
yarn start      # or npm start
```

**Backend environment variables** (`backend/.env`):

| Variable | Required? | Purpose |
| --- | --- | --- |
| `MONGO_URL` | **Required** | Full MongoDB connection string. No default — `backend/db.py` reads it with `os.environ[...]`, so the app fails to start without it. |
| `DB_NAME` | **Required** | Name of the MongoDB database to use. Same hard-required pattern as `MONGO_URL`. |
| `EMERGENT_LLM_KEY` | **Required for any AI feature** | The key `llm_service.py` and `poc_core.py` pass to `emergentintegrations`. Currently Emergent-issued — see [Section VII](#vii-self-hosting--migration-status) for what this means for a fully independent deployment. |
| `KHOVA_ADMIN_EMAILS` | Optional (default `admin@khova.ai`) | Comma-separated list of emails granted the `admin` role (bypasses credit/entitlement checks, can issue redeem codes, sees `/config/models`, `/admin/*`). **Set this explicitly before going live** — the shipped default is a public, predictable value baked into this repo's source, not a real credential. |
| `CORS_ORIGINS` | **Required in practice** (no usable default) | Comma-separated list of allowed frontend origins. The backend sets `allow_credentials=True` for cookie-based auth, and browsers refuse to honor a wildcard `Access-Control-Allow-Origin` together with credentialed requests — so leaving this unset breaks cross-origin login silently. The app now fails to start if `CORS_ORIGINS` is left at its `*` default, unless `KHOVA_ALLOW_WILDCARD_CORS=true` is set (same-origin local dev only — never set this in a real deployment). |
| `KHOVA_TRUST_PROXY_HEADERS` | Optional (default `false`) | Whether `ratelimit.client_ip()` trusts `X-Forwarded-For`/`X-Real-IP` for the anonymous rate limiter. Only set this to `true` if the app sits behind a reverse proxy that overwrites (not appends to) those headers before your app sees them — otherwise any caller can spoof a fresh IP per request and bypass the free-tier AI rate limit entirely. Left at the default `false`, the limiter uses the actual socket peer address instead. |
| `KHOVA_ANON_MAX_AI`, `KHOVA_ANON_WINDOW_SEC`, `KHOVA_ANON_MIN_INTERVAL_SEC`, `KHOVA_ANON_COOLDOWN_SEC`, `KHOVA_ANON_DEDUP_SEC` | Optional | Tune the anonymous-funnel rate limiter (defaults: 8 requests / 3600s window, 3s minimum gap between requests, 600s cooldown once blocked, 30s duplicate-request window). See [Section V](#v-application-processing-pipeline). |

**Frontend environment variables** (`frontend/.env`):

| Variable | Required? | Purpose |
| --- | --- | --- |
| `REACT_APP_BACKEND_URL` | **Required** | Base URL the frontend's API client (`frontend/src/lib/api.js`) sends every request to. |

**Running the backend test suite:** `cd backend && pytest -q` (fixed at 2 parallel workers via `pytest.ini`'s `-n 2 --dist loadscope`; run serially with `pytest -q -n 0` if needed).

---

## **V. Application Processing Pipeline**

This is what actually happens on the backend between a wizard action and a persisted result — the counterpart to Section IV from the server's point of view.

1. **Every expensive AI call runs inside a tracked generation job** (`backend/jobs.py`). A job moves `running` → `completed` | `failed`; it is never silently retried or left dangling.
2. **For an authenticated user**, starting a job (`jobs.begin`) checks, in order: (a) the task's required feature is enabled on the user's plan, (b) — only for tasks that start a brand-new product (`ebook_plan`, `spreadsheet_spec`, `website_spec`) and only if this project hasn't already been counted — the free-tier creation limit, (c) fewer than 3 recent failures of this exact task on this project in the last 10 minutes (retry-limit protection), (d) no identical task already `running` on this project in the last 90 seconds (duplicate-job protection), and (e) sufficient credit balance for the task's cost. Any failure raises a specific domain exception (`FeatureLocked`, `InsufficientCredits`, `CreationLimitReached`, `DuplicateJob`, `RetryLimitReached`), mapped to the matching HTTP status in `server.py`.
3. **Credits are reserved, then charged only on success** — a job that fails before completing costs the user nothing. If credits were charged and the job later needs to be marked failed anyway (the defensive charged-then-failed path), `jobs.fail` atomically refunds them.
4. **For an anonymous visitor** (deferred-auth funnel steps only), `jobs.begin`'s checks are skipped entirely; instead `ratelimit.enforce_anon` runs first, keyed by client IP (resolved from `X-Forwarded-For`/`X-Real-IP`, honoring an ingress proxy). It checks, in order: an active cooldown block, a minimum-interval rapid-fire guard, a duplicate/simultaneous request within a short dedup window, and finally a rolling-window request count — exceeding the window count applies a cooldown block for repeat probing. The request is still logged as a job (for usage visibility) but is never charged credits.
5. **Model routing happens per task, not per user choice** (`backend/model_router.py`): each task is classified into a `low`/`mid`/`high` complexity tier, and each tier maps to a fixed provider+model pair from `llm_service.DEFAULT_MODELS` — cheap/fast for classification, metadata, and formatting; a stronger model for research synthesis, long-form writing, strategy, and QA. This routing decision is recorded on the job but never exposed to normal users (`GET /config/models` is admin-only).
6. **`agents.py` functions build the actual prompt/response for each stage** and call into `llm_service.py`'s `llm_json`/`llm_text` (structured or free-text generation), `research` (Gemini/Anthropic web-search-grounded search with real citation extraction), or `generate_image` (Nano Banana image generation, base64-decoded to bytes). Structured JSON responses are parsed defensively — code-fence stripping, outermost-brace extraction, and one retry with an explicit "return only valid JSON" instruction before giving up.
7. **Deterministic steps never touch the AI layer.** Applying one of the five website style presets, rebuilding a website's HTML after a style change, building the final PDF/XLSX/HTML exports, and zipping a product's assets into a downloadable bundle are all pure code in `exporters.py`/`server.py` — no credits are charged and no AI call happens for any of them.
8. **Every project change is persisted immediately** (`save_project`) after the step that produced it, so a project can be resumed from wherever it was left, and `current_step`/`status` always reflect the furthest completed stage.
9. **Publishing a website snapshots the current draft** rather than serving it live: `website/publish` deep-copies the spec and rendered HTML into `website.published`, so further edits to the draft don't change what's already public until the user explicitly republishes. `GET /api/sites/{slug}` serves the published snapshot by default, or the live draft with `?preview=1`.

---

## **VI. Database Schema**

The application persists one document per collection entity in MongoDB (`backend/db.py`); there is no formal migration tool (e.g. no Alembic-equivalent) — a Mongo collection's shape is whatever the code currently writes to it.

<details>
<summary><b>View Collection Shapes (Click to expand)</b></summary>

### 1. `projects`

The core document — one per digital product being built, holding the entire pipeline's state as it progresses.

| Field | Notes |
| --- | --- |
| `id` | `prj_<12 hex chars>` |
| `user_id` | Owning user's `user_id`, or `null` for an anonymous (not-yet-claimed) project |
| `title` | Defaults to a placeholder ("Produk Baru") until set |
| `status` | e.g. `draft`, `complete` |
| `current_step` | Furthest-reached pipeline stage (`discover`, `research`, ..., `export`) |
| `ui_language` / `product_language` | Independently configurable (default `id` — Indonesian) |
| `models_config` | Optional per-project override of the default provider/model per task category |
| `discover` | Free-text idea, optional expertise/audience/interests/uploaded-material context |
| `research` | Research findings bundle: text + `{title, url, finding, relevance}` sources |
| `opportunities` | List of generated/scored opportunities |
| `selected_opportunity_id` | Which opportunity the user committed to |
| `positioning`, `transformation` | Positioning statement and the six-part transformation map |
| `format` | Chosen product format |
| `ebook` / `spreadsheet` / `website` | Format-specific generated content (only the chosen format is populated) |
| `qa` | List of QA review results/applied fixes |
| `branding` | Generated name/tagline/visual-identity text |
| `assets` | Generated downloadable files (PDF/XLSX/PNG/HTML), each with `id`, `type`, `filename`, `path`, `mime` |
| `counted_as_creation` | Whether this project has already consumed one of the user's free-tier creation slots |
| `created_at` / `updated_at` | Timestamps |

### 2. `users`

| Field | Notes |
| --- | --- |
| `user_id` | `user_<12 hex chars>` |
| `email`, `name`, `picture` | From the auth provider |
| `role` | `user` or `admin` (derived from `KHOVA_ADMIN_EMAILS` on every login) |
| `plan` | `free` / `creator` / `pro` |
| `credits` | Current balance, mutated only via the atomic ledger operations in `billing.py` |
| `creations_used` | Free-tier full-product creation counter |
| `created_at` | Account creation timestamp |

### 3. `user_sessions`

| Field | Notes |
| --- | --- |
| `user_id`, `session_token` | `session_token` is set as an `httponly`, `secure`, `samesite=none` cookie |
| `expires_at` | 7 days from creation |
| `created_at` | |

### 4. `credit_ledger`

An append-only log backing every credit mutation — never mutated in place, always inserted alongside the atomic `users.credits` update that caused it.

| Field | Notes |
| --- | --- |
| `id` | `led_<12 hex chars>` |
| `user_id`, `delta`, `reason`, `task`, `job_id` | What changed, why, and which job (if any) caused it |
| `balance_after` | Balance snapshot immediately after this entry, for easy auditing without replaying the whole log |
| `created_at` | |

### 5. `generation_jobs`

One row per AI generation attempt (see [Section V](#v-application-processing-pipeline)).

| Field | Notes |
| --- | --- |
| `id` | `job_<12 hex chars>` |
| `user_id` | `null` for anonymous funnel jobs |
| `project_id`, `task` | Which project, which pipeline task |
| `tier`, `provider`, `model` | The routing decision from `model_router.route()` |
| `estimated_credits` / `credits_charged` | Reserved vs. actually charged (0 unless completed) |
| `status` | `running` / `completed` / `failed` |
| `retry_count`, `error` | Incremented and set on every failure |
| `started_at`, `completed_at`, `created_at` | |

### 6. `redeem_codes` / `redemptions_log`

| `redeem_codes` field | Notes |
| --- | --- |
| `code` | `<PREFIX>-XXXX-XXXX`, admin-generated |
| `plan`, `credits` | What redeeming grants |
| `max_redemptions`, `redemptions` | Atomically incremented on redeem; auto-deactivated once exhausted |
| `expires_at`, `active` | |

| `redemptions_log` field | Notes |
| --- | --- |
| `code`, `user_id`, `plan`, `credits`, `at` | One row per successful redemption — also enforces "already redeemed by this user" |

### 7. `anon_ai_usage` / `anon_blocks`

Backing collections for the anonymous rate limiter ([Section V](#v-application-processing-pipeline)). Both carry a Mongo TTL index so old entries expire automatically and the collections can't grow unbounded.

| `anon_ai_usage` field | Notes |
| --- | --- |
| `id`, `ip`, `task`, `project_id`, `at` | One row per anonymous AI request; also used to detect duplicate/rapid-fire requests |

| `anon_blocks` field | Notes |
| --- | --- |
| `ip`, `blocked_until`, `reason`, `at` | One row per IP currently under a cooldown block |

</details>

---

## **VII. Self-Hosting & Migration Status**

The project was originally scaffolded and run on [Emergent](https://emergent.sh/), and this fork's purpose is to move it off that platform. **This is in progress, not finished** — two integration points in the current codebase are still tied to Emergent's own infrastructure, independent of where the FastAPI/React/MongoDB processes themselves happen to run.

### A. What's harmless leftover

The `.emergent/` folder (`emergent.yml`, `markers`, `cron`, `system_deps.txt`, `emergent_todos.json`) is Emergent's own bootstrap/orchestration bookkeeping for its dashboard — the base container image tag and some restore markers and cron/webhook scripts. **No application code reads this folder.** It's safe to delete or `.gitignore` it in a self-hosted fork.

Similarly, `@emergentbase/visual-edits` (referenced in `frontend/craco.config.js`) is Emergent's live visual-editing dev tool. It's wrapped in a try/catch and only loads in dev mode — if the package is absent, it just logs a warning and no-ops. Not a blocker.

### B. What's still Emergent-specific

**1. Login is Emergent's hosted Google-auth broker, not a portable Google OAuth integration.**
`frontend/src/context/AuthContext.js` redirects the browser straight to `https://auth.emergentagent.com/?redirect=...`, and `backend/auth.py`'s `/api/auth/session` route validates the `session_id` that flow returns against `https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data`. This is Emergent's own managed identity service, not "Google OAuth configured with Emergent's client ID" — there's no environment variable that points it at a self-owned Google Cloud OAuth client instead. Outside Emergent's platform, this flow won't authenticate anyone. The only thing that currently works off-platform is `/api/auth/dev-login`, which the code itself comments as a **test-only bypass to remove before production**. Fully self-hosting requires implementing an independent Google OAuth2 flow (a Google Cloud Console project + client library such as `authlib`) and retiring `dev-login`.

**2. AI access goes through Emergent's metered "Universal Key," not direct provider keys.**
`backend/llm_service.py` and `backend/poc_core.py` both import `emergentintegrations.llm.chat.LlmChat` and read `EMERGENT_LLM_KEY`. Two separate issues:
   - `emergentintegrations` is not on public PyPI; it's distributed through Emergent's own private package index, so a plain `pip install -r requirements.txt` fails on that line outside Emergent's build environment unless the correct `--extra-index-url` is supplied.
   - `EMERGENT_LLM_KEY` is an Emergent-issued, Emergent-billed key, not a drop-in replacement for a personal OpenAI/Anthropic/Gemini API key — the whole point of that key is that Emergent proxies and meters spend across providers on the caller's behalf.

   `requirements.txt` already lists `openai`, `google-generativeai`, and `google-genai` directly, so the codebase was written with provider abstraction in mind: swapping `llm_service.py`'s internals to call those SDKs directly with independently-issued keys is a bounded refactor of one file, not a rewrite. `model_router.py` (the tier/task routing logic) sits above `llm_service.py` and doesn't need to change at all.

**3. `litellm` is pinned to a direct wheel URL on Emergent's own CDN**, not a normal PyPI release (`requirements.txt`: `litellm @ https://customer-assets.emergentagent.com/...`). It will likely keep working as a plain HTTPS download, but it's a single point of failure outside anyone's control — worth repinning to a standard PyPI `litellm` version unless there's a specific reason to keep the pinned wheel.

### C. What's already portable

- The FastAPI backend and MongoDB access (via Motor) are completely standard — they work against any MongoDB instance (self-hosted or a managed provider) once `MONGO_URL`/`DB_NAME` point at it.
- The React/CRA frontend already reads its backend URL from `REACT_APP_BACKEND_URL` and the backend already reads its allowed origins from `CORS_ORIGINS`, so pointing frontend↔backend at new hosts is a config change, not a code change.
- WeasyPrint (PDF export) and openpyxl (XLSX export) are plain Python libraries with no Emergent coupling — just make sure the host's OS has WeasyPrint's system dependencies (Cairo, Pango, GDK-PixBuf) installed, since that's easy to miss outside a prebuilt container image.
- `stripe` is listed in `requirements.txt` but isn't actually called anywhere in `billing.py` yet — there's no real payment processing to unwind, but also nothing wired up to rely on yet.

**Bottom line:** the two real blockers to a fully independent deployment are auth (needs a real Google OAuth2 implementation) and the LLM layer (needs direct provider SDK calls instead of `emergentintegrations`/`EMERGENT_LLM_KEY`). Everything else — the `.emergent/` metadata, the visual-edits dev tool, the pinned `litellm` wheel, and the database/frontend/PDF/XLSX layers — is either inert or a straightforward config change.

---

## **VIII. FAQ**

### **A. "Why is opportunity/research/positioning/transformation free, but product generation isn't?"**

<details>
<summary><b>View Explanation (Click to expand)</b></summary>

The discovery funnel exists so a visitor can evaluate whether Khova AI would actually produce something useful for their idea *before* committing to an account or spending credits. Charging credits (and requiring login) only starts once the user commits to a specific format and asks the app to actually write/build the product — that's also where the real generation cost (long-form writing, cover/illustration image generation, spreadsheet/website content) lives. See [Section IV.C](#c-plans--credits) and [Section V](#v-application-processing-pipeline).

</details>

### **B. "Why does the anonymous funnel have its own separate rate limiter instead of just the credit system?"**

<details>
<summary><b>View Explanation (Click to expand)</b></summary>

The credit system only applies to logged-in users — it can't protect a route that runs before anyone has an account. Since the discovery funnel runs real AI calls for free specifically to let anonymous visitors explore, it needs its own protection against abuse (scripted probing, cost farming) that doesn't depend on an account existing. That's `ratelimit.py`: a sliding window plus cooldown, keyed by client IP rather than by user or session, checked *before* any AI call is made. Authenticated users never pass through this module — they're governed entirely by the plan/credit/entitlement system in `jobs.py`/`billing.py` instead.

</details>

### **C. "Why does the app pick the AI provider and model instead of letting users choose?"**

<details>
<summary><b>View Explanation (Click to expand)</b></summary>

`backend/model_router.py`'s docstring states this directly: users never select a provider or model. Khova decides, per task, which provider/model/tier to use based on the task's complexity, expected quality, and cost — cheap/fast models for classification and formatting, stronger models for research synthesis, long-form writing, and QA. This keeps the product experience simple (no model-picker UI to explain) and keeps cost control centralized in one place rather than spread across every agent call site. The routing decision is still recorded per job for admin visibility (`GET /config/models`, admin-only) and usage auditing — it just isn't exposed to normal users.

</details>

### **D. "What happens if a generation step fails partway through?"**

<details>
<summary><b>View Explanation (Click to expand)</b></summary>

Credits are reserved-then-charged, not charged upfront: a job only actually deducts credits on successful completion (`jobs.complete`). If the AI call itself raises an exception, or an `HTTPException` is raised anywhere in the route, the job is marked `failed` and any credits that *were* already charged (the defensive charged-then-failed path) are atomically refunded. Retry protection then caps repeated failures on the exact same task/project to 3 within a 10-minute window, and duplicate-job protection blocks starting the same task again while an attempt from the last 90 seconds is still `running` — both independent of whether a failure was refunded.

</details>

### **E. "Is a published website's URL stable if I keep editing the draft?"**

<details>
<summary><b>View Explanation (Click to expand)</b></summary>

Yes. Publishing (`POST /projects/{id}/website/publish`) deep-copies the current spec and rendered HTML into a separate `website.published` snapshot at that moment. `GET /api/sites/{slug}` serves that snapshot by default — further edits to the editable draft (including a style-preset change, which rebuilds `draft_html` deterministically with no AI call) don't touch what's already public until the project owner explicitly republishes. Appending `?preview=1` to the site URL serves the current draft instead, for the owner to check their in-progress edits before republishing.

</details>

---

## **IX. Third-Party Services & Legal Notes**

This project depends on a few external services. **Nothing here is a substitute for reading each service's actual current terms** — this section is a summary, not a legal opinion, and the app is a portfolio/collaborative project, not a commercial product with its own legal review.

- **AI providers (OpenAI, Google Gemini, Anthropic), currently proxied through Emergent's `emergentintegrations`/`EMERGENT_LLM_KEY`.** All AI-generated content — research summaries, opportunity descriptions, transformation maps, eBook/spreadsheet/website copy, branding text, and generated images — is subject to the terms of whichever underlying provider actually served the request, in addition to Emergent's own terms for the intermediary key while that dependency remains in place (see [Section VII](#vii-self-hosting--migration-status)). AI-generated text and images should be treated as a generated draft, not an independently verified authoritative source, particularly for the `RESEARCH-BACKED` vs. `HYPOTHESIS` vs. `ASSUMPTION` labeling described in [Section I](#i-short-description) — that labeling reflects the model's own claimed confidence, not independent fact-checking by this application.
- **Real-time web research.** Market-research findings are gathered live via provider-hosted web-search grounding (Gemini's `googleSearch` tool, or Anthropic's web-search tool, depending on routing) at generation time; they are not pre-scraped or redistributed as a static dataset by this project. Anyone building on the retained `{title, url, finding, relevance}` source records should independently verify a source before relying on it, rather than treating the AI's summary of it as authoritative.
- **Emergent (`emergent.sh`).** Two parts of the current codebase — the Google-login broker and the LLM access key/package — depend on Emergent's own hosted services rather than being self-contained; see [Section VII](#vii-self-hosting--migration-status) for exactly what that means and what replacing it involves. This is expected to change as the migration continues.
- **No warranty.** This project is provided for educational/portfolio purposes. Generated digital products (research findings, opportunity scores, product content, exported files) should be independently reviewed before being published, sold, or relied upon — neither the market research nor the generated product content is guaranteed accurate, complete, or current.
