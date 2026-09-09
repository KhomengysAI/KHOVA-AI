#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Khova AI — Final V1 hardening. Harden existing mature app without rebuilding: (1) anonymous AI rate limiting, (2) cost safety, (3) product bundle ZIP download, (4) auto-refund UX, (5) deterministic website themes, (6) usage insights, (7) server-authoritative security, (8) localization preserved, (9) no regression of Phase 3+4 (48/48)."

backend:
  - task: "Anonymous AI rate limiting (server-side, IP-based, configurable)"
    implemented: true
    working: true
    file: "ratelimit.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "New ratelimit.py enforces anon exploration limits keyed by client IP (X-Forwarded-For aware). Config via env: KHOVA_ANON_MAX_AI(8), WINDOW_SEC(3600), MIN_INTERVAL_SEC(3), COOLDOWN_SEC(600), DEDUP_SEC(30). Checks order: active cooldown -> rapid-fire -> duplicate -> rolling window (sets cooldown when exceeded). Wired into run_ai anonymous branch for research/opportunities/positioning/transformation. Returns 429 with structured detail {message,code,retry_after,anon_limited}. Authenticated users skip this entirely. Local mocked tests pass (allowed<limit, blocked after, cooldown, duplicate, too_fast, auth bypass, server-side record count)."
        - working: true
          agent: "testing"
          comment: "LIVE VERIFIED: (1) Duplicate request blocked with 429 + structured detail {message:'This request is already being processed...', code:'anon_duplicate', retry_after:30, anon_limited:true}. (2) Authenticated user bypasses anon limit entirely on same project. Both tests used real AI (2 calls total). Rate limiting works correctly before AI executes (cost-safe)."
  - task: "Product bundle ZIP download (deterministic, ownership-checked)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "GET /api/projects/{id}/bundle (auth required). Packages pdf/xlsx/bonus/html assets into one ZIP in-memory (no AI). Dedups filenames, skips missing files, 400 when none, 403 for non-owner (admin allowed). Local tests pass."
        - working: true
          agent: "testing"
          comment: "LIVE VERIFIED: (1) Unauthenticated request -> 401. (2) Non-owner request -> 403. (3) Owner request with no assets -> 400 with 'No downloadable assets' message. All security/edge cases pass."
  - task: "Auto-refund plumbing + structured failure payloads (Priority 4)"
    implemented: true
    working: true
    file: "jobs.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "jobs.fail now refunds credits_charged>0 via billing.refund_credits and returns refunded amount (charge-on-success preserved; normal pre-completion failures refund 0 since nothing was charged). run_ai raises 502 with detail {message,code,refunded,balance}. Unit test verifies real refund + no false refund on no-charge failure."
        - working: true
          agent: "testing"
          comment: "VERIFIED via in-repo suite: refund logic passes all tests (charged job refunds, balance restored, no false refund on no-charge failure). Not tested live to avoid triggering real failures."
  - task: "Website theme presets deterministic apply (Priority 5)"
    implemented: true
    working: true
    file: "exporters.py, server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "STYLE_PRESETS expanded (typography/spacing/radius/button/hierarchy) for Minimal/Modern/Premium/Editorial/Bold. New PATCH /api/projects/{id}/website/style applies a preset deterministically (no AI), rebuilds draft preview, persists; invalid preset 400. Canonical palette NOT replaced (verified primary color still present in all 5 renders)."
        - working: true
          agent: "testing"
          comment: "LIVE VERIFIED: (1) Theme change without spec -> 400 with 'spec' in error. (2) Invalid theme 'Rainbow' -> 400 with 'theme' in error. Edge cases pass. In-repo suite confirms all 5 presets render + palette canonical."
  - task: "Usage insights endpoint (own data only) (Priority 6)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "GET /api/me/usage returns credits_remaining, total_credits_used, total_credits_refunded, total_generations, product_generations, per-product breakdown. Scoped strictly to authenticated user_id (verified another user's jobs on same project id do not leak)."
        - working: true
          agent: "testing"
          comment: "LIVE VERIFIED: (1) Requires auth (401 without). (2) Fresh user returns zeros for all totals + empty products array. (3) Each user sees only their own data (scoped correctly). All keys present: credits_remaining, total_credits_used, total_credits_refunded, total_generations, product_generations, products."
  - task: "Environment recovery (.env recreated, empty DB)"
    implemented: true
    working: true
    file: "backend/.env, frontend/.env"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Env had been reset: both .env files missing + empty Mongo -> backend was crash-looping (KeyError MONGO_URL). Recreated backend/.env (MONGO_URL, DB_NAME=test_database, EMERGENT_LLM_KEY, KHOVA_ADMIN_EMAILS, KHOVA_ANON_* config) and frontend/.env (REACT_APP_BACKEND_URL, WDS_SOCKET_PORT). Backend healthy again."
  - task: "Security / Server-Authority (Priority 7)"
    implemented: true
    working: true
    file: "server.py, model_router.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "LIVE VERIFIED: (1) GET /api/config/models: normal user -> 403, admin -> 200. (2) PUT /api/settings: models_config ignored/stripped from response. (3) GET /api/admin/overview: normal user -> 403, admin -> 200 with users/jobs keys. (4) GET /api/me/economy: returns server-authoritative plan/credits/features. All security checks pass."

frontend:
  - task: "Refund-aware error UX + anon-limit sign-in prompt"
    implemented: true
    working: "NA"
    file: "lib/api.js, lib/economy.js, steps/*"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Axios error interceptor normalizes dict `detail` -> string + exposes _refund/_structured, refreshes credits pill on refund. generationErrorMessage() shows refund text only when a refund actually occurred. Funnel steps (research/opportunities/positioning/transformation) show anon-limit message and open the login modal on 429. NOT YET UI-TESTED (awaiting user go-ahead)."
  - task: "Download Product Bundle button (ExportStep)"
    implemented: true
    working: "NA"
    file: "steps/ExportStep.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Blob download with success/error toasts; disabled when no assets. NOT YET UI-TESTED."
  - task: "Website theme selector (deterministic) + Usage Insights card (Settings)"
    implemented: true
    working: "NA"
    file: "steps/WebsiteCreator.js, pages/Settings.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "WebsiteCreator theme Select applies preset via API + refreshes preview (cache-busted iframe). Settings shows Usage Insights (remaining/used/generations + per-product bars). NOT YET UI-TESTED."

metadata:
  created_by: "main_agent"
  version: "2.1"
  test_sequence: 2
  run_ui: false

test_plan:
  current_focus:
    - "Anonymous AI rate limiting (server-side, IP-based, configurable)"
    - "Product bundle ZIP download (deterministic, ownership-checked)"
    - "Auto-refund plumbing + structured failure payloads (Priority 4)"
    - "Website theme presets deterministic apply (Priority 5)"
    - "Usage insights endpoint (own data only) (Priority 6)"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "Final hardening implemented. Environment had been reset (missing .env + empty DB) — recovered. All work is COST-SAFE with mocked AI. Local suite: 80/80 assertions pass (original 48 + 32 new). Please retest BACKEND ONLY (do not touch frontend). Focus: (1) anon rate limiting via /api/projects/{id}/research using X-Forwarded-For header — note limits are env-configurable (defaults MAX=8/window=3600s/min_interval=3s/cooldown=600s/dedup=30s); to force blocking quickly set a distinct X-Forwarded-For and send >8 requests, or verify duplicate (same task+project within 30s) returns 429. DO NOT run real AI beyond a couple of research calls; the research agent is live AI but cheap — keep calls minimal. Auth via POST /api/auth/dev-login {email,name}; admin email admin@khova.ai. (2) bundle download ownership + zip. (3) /api/me/usage scoping. (4) website/style deterministic + palette canonical. (5) confirm authenticated credit flow untouched. Use dev-login; credentials in /app/memory/test_credentials.md."
    - agent: "testing"
      message: "FINAL HARDENING VERIFICATION COMPLETE. All backend features tested and working. Results: (1) Anonymous AI rate limiting: ✅ PASS - duplicate blocking works, auth bypass works, structured 429 responses correct. (2) Product bundle download: ✅ PASS - auth required, ownership enforced, no-assets returns 400. (3) Usage insights: ✅ PASS - auth required, fresh user zeros, scoped per-user. (4) Website theme: ✅ PASS - requires spec, invalid theme rejected. (5) Security/server-authority: ✅ PASS - admin endpoints protected, models_config ignored, economy server-authoritative. (6) REGRESSION: ✅ 80/80 in-repo cost-safe suite passed. AI calls: 2/3 (under budget). NO ISSUES FOUND. Ready for user acceptance."
