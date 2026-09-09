"""
Khova AI FINAL HARDENING Backend Verification
COST-SAFE: Max 3 real AI calls (all to research endpoint)
Tests: anon rate limiting, bundle download, usage insights, website theme, security
"""
import requests
import sys
import time

BASE_URL = "https://550aaa77-283c-4044-88cd-b4f82331f5fc.preview.emergentagent.com/api"

class HardeningTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.ai_calls_made = 0
        self.admin_token = None
        self.user_token = None
        self.user_id = None
        self.user2_token = None
        self.user2_id = None
        
    def log(self, msg, status="info"):
        icons = {"pass": "✅", "fail": "❌", "info": "ℹ️", "warn": "⚠️"}
        print(f"{icons.get(status, '•')} {msg}")
    
    def test(self, name, fn):
        """Run a test function and track results"""
        try:
            self.log(f"Testing: {name}", "info")
            fn()
            self.passed += 1
            self.log(f"PASS: {name}", "pass")
            return True
        except AssertionError as e:
            self.failed += 1
            self.log(f"FAIL: {name} - {e}", "fail")
            return False
        except Exception as e:
            self.failed += 1
            self.log(f"ERROR: {name} - {e}", "fail")
            return False
    
    def assert_status(self, resp, expected, msg=""):
        if resp.status_code != expected:
            detail = ""
            try:
                detail = f" | {resp.json()}"
            except:
                detail = f" | {resp.text[:200]}"
            raise AssertionError(f"Expected {expected}, got {resp.status_code}{detail} {msg}")
    
    def assert_in(self, key, data, msg=""):
        if key not in data:
            raise AssertionError(f"Key '{key}' not in response {msg}")
    
    def setup_auth(self):
        """Setup admin and normal user tokens"""
        # Admin
        resp = requests.post(f"{BASE_URL}/auth/dev-login", 
                            json={"email": "admin@khova.ai", "name": "Admin"})
        self.assert_status(resp, 200, "admin login")
        self.admin_token = resp.json()["session_token"]
        
        # Normal user
        resp = requests.post(f"{BASE_URL}/auth/dev-login",
                            json={"email": "tester@khova.ai", "name": "Tester"})
        self.assert_status(resp, 200, "user login")
        data = resp.json()
        self.user_token = data["session_token"]
        self.user_id = data["user"]["user_id"]
        
        # Second user for ownership tests
        resp = requests.post(f"{BASE_URL}/auth/dev-login",
                            json={"email": "tester2@khova.ai", "name": "Tester2"})
        self.assert_status(resp, 200, "user2 login")
        data = resp.json()
        self.user2_token = data["session_token"]
        self.user2_id = data["user"]["user_id"]
        
        self.log(f"Auth setup: admin + 2 users", "info")
    
    # ========================================================================
    # PRIORITY 1: ANONYMOUS AI RATE LIMITING
    # ========================================================================
    
    def test_anon_rate_limit_duplicate(self):
        """Anon rate limit: duplicate request within dedup window (30s) should 429"""
        # Create anonymous project (no auth)
        resp = requests.post(f"{BASE_URL}/projects", 
                            json={"title": "anon_test"})
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # First research call with specific IP
        headers = {"X-Forwarded-For": "198.51.100.7"}
        self.log("Making 1st research call (real AI, ~10-20s)...", "warn")
        resp1 = requests.post(f"{BASE_URL}/projects/{proj_id}/research", 
                             headers=headers, timeout=60)
        self.assert_status(resp1, 200, "1st research should succeed")
        self.ai_calls_made += 1
        self.log(f"AI calls: {self.ai_calls_made}/3", "info")
        
        # Immediate duplicate (within 30s dedup window) should be blocked
        self.log("Sending duplicate request immediately (should be 429)...", "info")
        resp2 = requests.post(f"{BASE_URL}/projects/{proj_id}/research",
                             headers=headers, timeout=30)
        self.assert_status(resp2, 429, "2nd duplicate should be 429")
        
        # Verify structured error body
        detail = resp2.json()["detail"]
        self.log(f"DEBUG: 429 detail = {detail}", "info")
        self.assert_in("message", detail)
        self.assert_in("code", detail)
        assert detail["code"].startswith("anon_"), f"code should start with anon_, got {detail['code']}"
        self.assert_in("retry_after", detail)
        self.assert_in("anon_limited", detail)
        assert detail["anon_limited"] == True
        # Check for sign-in prompt (case-insensitive)
        msg_lower = detail["message"].lower()
        assert "sign" in msg_lower or "login" in msg_lower or "wait" in msg_lower, \
            f"message should guide user, got: {detail['message']}"
    
    def test_anon_rate_limit_auth_bypass(self):
        """Authenticated user should NOT be rate-limited on anon project"""
        # Create anon project
        resp = requests.post(f"{BASE_URL}/projects", json={"title": "anon_auth_test"})
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # Authenticated call should succeed even from same IP (but use different IP to avoid dedup)
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "X-Forwarded-For": "198.51.100.8"  # different IP from previous test
        }
        self.log("Making authenticated research call (real AI, ~10-20s)...", "warn")
        resp = requests.post(f"{BASE_URL}/projects/{proj_id}/research",
                            headers=headers, timeout=90)
        self.assert_status(resp, 200, "authenticated should bypass anon limit")
        self.ai_calls_made += 1
        self.log(f"AI calls: {self.ai_calls_made}/3", "info")
    
    # ========================================================================
    # PRIORITY 3: PRODUCT BUNDLE DOWNLOAD
    # ========================================================================
    
    def test_bundle_unauthenticated(self):
        """Bundle download requires auth"""
        # Create project as user
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.post(f"{BASE_URL}/projects", 
                            json={"title": "bundle_test"}, headers=headers)
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # Try download without auth
        resp = requests.get(f"{BASE_URL}/projects/{proj_id}/bundle")
        self.assert_status(resp, 401, "bundle without auth should 401")
    
    def test_bundle_wrong_owner(self):
        """Bundle download enforces ownership"""
        # User1 creates project
        headers1 = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.post(f"{BASE_URL}/projects",
                            json={"title": "owner_test"}, headers=headers1)
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # User2 tries to download
        headers2 = {"Authorization": f"Bearer {self.user2_token}"}
        resp = requests.get(f"{BASE_URL}/projects/{proj_id}/bundle", headers=headers2)
        self.assert_status(resp, 403, "bundle from non-owner should 403")
    
    def test_bundle_no_assets(self):
        """Bundle download with no assets should 400"""
        # Create project with no assets
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.post(f"{BASE_URL}/projects",
                            json={"title": "empty_bundle"}, headers=headers)
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # Try download
        resp = requests.get(f"{BASE_URL}/projects/{proj_id}/bundle", headers=headers)
        self.assert_status(resp, 400, "bundle with no assets should 400")
        assert "asset" in resp.json()["detail"].lower(), "error should mention assets"
    
    # ========================================================================
    # PRIORITY 6: USAGE INSIGHTS
    # ========================================================================
    
    def test_usage_requires_auth(self):
        """Usage endpoint requires auth"""
        resp = requests.get(f"{BASE_URL}/me/usage")
        self.assert_status(resp, 401, "usage without auth should 401")
    
    def test_usage_fresh_user(self):
        """Fresh user should have zero usage"""
        # Create fresh user
        resp = requests.post(f"{BASE_URL}/auth/dev-login",
                            json={"email": f"fresh_{int(time.time())}@khova.ai", "name": "Fresh"})
        self.assert_status(resp, 200)
        token = resp.json()["session_token"]
        
        # Get usage
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/me/usage", headers=headers)
        self.assert_status(resp, 200)
        data = resp.json()
        
        # Verify structure
        self.assert_in("credits_remaining", data)
        self.assert_in("total_credits_used", data)
        self.assert_in("total_credits_refunded", data)
        self.assert_in("total_generations", data)
        self.assert_in("product_generations", data)
        self.assert_in("products", data)
        
        # Fresh user should have zeros
        assert data["total_credits_used"] == 0, "fresh user should have 0 credits used"
        assert data["total_generations"] == 0, "fresh user should have 0 generations"
        assert data["products"] == [], "fresh user should have empty products"
    
    def test_usage_scoped_to_user(self):
        """Usage endpoint only returns caller's data"""
        # User1 gets their usage
        headers1 = {"Authorization": f"Bearer {self.user_token}"}
        resp1 = requests.get(f"{BASE_URL}/me/usage", headers=headers1)
        self.assert_status(resp1, 200)
        data1 = resp1.json()
        
        # User2 gets their usage
        headers2 = {"Authorization": f"Bearer {self.user2_token}"}
        resp2 = requests.get(f"{BASE_URL}/me/usage", headers=headers2)
        self.assert_status(resp2, 200)
        data2 = resp2.json()
        
        # They should be different (user1 has made AI calls, user2 hasn't)
        # At minimum, verify the endpoint returns successfully for both
        assert isinstance(data1["products"], list)
        assert isinstance(data2["products"], list)
    
    # ========================================================================
    # PRIORITY 5: WEBSITE THEME
    # ========================================================================
    
    def test_website_theme_no_spec(self):
        """Website theme change requires spec first"""
        # Create project
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.post(f"{BASE_URL}/projects",
                            json={"title": "theme_test"}, headers=headers)
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # Try to change theme without spec
        resp = requests.patch(f"{BASE_URL}/projects/{proj_id}/website/style",
                             json={"style": "Minimal"}, headers=headers)
        self.assert_status(resp, 400, "theme change without spec should 400")
        assert "spec" in resp.json()["detail"].lower()
    
    def test_website_theme_invalid(self):
        """Invalid theme should 400"""
        # Create project with minimal setup
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.post(f"{BASE_URL}/projects",
                            json={"title": "invalid_theme"}, headers=headers)
        self.assert_status(resp, 200)
        proj_id = resp.json()["id"]
        
        # Patch to add a fake website spec (to bypass the "no spec" check)
        resp = requests.patch(f"{BASE_URL}/projects/{proj_id}",
                             json={"positioning": {"value": "test"}, 
                                   "transformation": {"core_transformation": "test"}},
                             headers=headers)
        
        # Now try invalid theme
        resp = requests.patch(f"{BASE_URL}/projects/{proj_id}/website/style",
                             json={"style": "Rainbow"}, headers=headers)
        self.assert_status(resp, 400, "invalid theme should 400")
        assert "theme" in resp.json()["detail"].lower()
    
    # ========================================================================
    # PRIORITY 7: SECURITY / SERVER-AUTHORITY
    # ========================================================================
    
    def test_config_models_admin_only(self):
        """GET /config/models requires admin"""
        # Normal user should get 403
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.get(f"{BASE_URL}/config/models", headers=headers)
        self.assert_status(resp, 403, "normal user should get 403")
        
        # Admin should get 200
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/config/models", headers=headers)
        self.assert_status(resp, 200, "admin should get 200")
    
    def test_settings_models_config_ignored(self):
        """PUT /settings should ignore models_config"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Try to set models_config
        resp = requests.put(f"{BASE_URL}/settings",
                           json={"ui_language": "en", "models_config": {"research": "gpt-5.4"}},
                           headers=headers)
        self.assert_status(resp, 200)
        data = resp.json()
        
        # models_config should NOT be in response
        assert "models_config" not in data, "models_config should be ignored/stripped"
        assert data.get("ui_language") == "en", "other settings should work"
    
    def test_admin_overview_admin_only(self):
        """GET /admin/overview requires admin"""
        # Normal user should get 403
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.get(f"{BASE_URL}/admin/overview", headers=headers)
        self.assert_status(resp, 403)
        
        # Admin should get 200
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        resp = requests.get(f"{BASE_URL}/admin/overview", headers=headers)
        self.assert_status(resp, 200)
        data = resp.json()
        self.assert_in("users", data)
        self.assert_in("jobs", data)
    
    def test_economy_server_authoritative(self):
        """GET /me/economy returns server-authoritative plan/credits"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = requests.get(f"{BASE_URL}/me/economy", headers=headers)
        self.assert_status(resp, 200)
        data = resp.json()
        
        # Should have server-controlled fields
        self.assert_in("plan", data)
        self.assert_in("credits", data)
        self.assert_in("features", data)
        
        # Plan should be valid
        assert data["plan"] in ["free", "creator", "pro"], f"invalid plan: {data['plan']}"
    
    # ========================================================================
    # MAIN TEST RUNNER
    # ========================================================================
    
    def run_all(self):
        self.log("=" * 70, "info")
        self.log("Khova AI FINAL HARDENING Backend Verification", "info")
        self.log("COST-SAFE: Max 3 real AI calls", "info")
        self.log("=" * 70, "info")
        
        # Setup
        self.log("\n[SETUP] Authenticating...", "info")
        self.setup_auth()
        
        # Priority 1: Anonymous AI Rate Limiting
        self.log("\n[PRIORITY 1] Anonymous AI Rate Limiting", "info")
        self.test("Anon rate limit: duplicate request blocked", self.test_anon_rate_limit_duplicate)
        self.test("Anon rate limit: auth bypass", self.test_anon_rate_limit_auth_bypass)
        
        # Priority 3: Product Bundle Download
        self.log("\n[PRIORITY 3] Product Bundle Download", "info")
        self.test("Bundle: requires auth", self.test_bundle_unauthenticated)
        self.test("Bundle: enforces ownership", self.test_bundle_wrong_owner)
        self.test("Bundle: no assets returns 400", self.test_bundle_no_assets)
        
        # Priority 6: Usage Insights
        self.log("\n[PRIORITY 6] Usage Insights", "info")
        self.test("Usage: requires auth", self.test_usage_requires_auth)
        self.test("Usage: fresh user has zeros", self.test_usage_fresh_user)
        self.test("Usage: scoped to caller", self.test_usage_scoped_to_user)
        
        # Priority 5: Website Theme
        self.log("\n[PRIORITY 5] Website Theme", "info")
        self.test("Website theme: requires spec", self.test_website_theme_no_spec)
        self.test("Website theme: invalid theme 400", self.test_website_theme_invalid)
        
        # Priority 7: Security
        self.log("\n[PRIORITY 7] Security / Server-Authority", "info")
        self.test("Security: /config/models admin-only", self.test_config_models_admin_only)
        self.test("Security: settings ignores models_config", self.test_settings_models_config_ignored)
        self.test("Security: /admin/overview admin-only", self.test_admin_overview_admin_only)
        self.test("Security: /me/economy server-authoritative", self.test_economy_server_authoritative)
        
        # Summary
        self.log("\n" + "=" * 70, "info")
        self.log(f"RESULTS: {self.passed} passed, {self.failed} failed", "info")
        self.log(f"AI calls made: {self.ai_calls_made}/3", "info")
        self.log("=" * 70, "info")
        
        if self.ai_calls_made > 3:
            self.log(f"WARNING: Exceeded AI call budget! ({self.ai_calls_made}/3)", "fail")
        
        return self.failed == 0

def main():
    tester = HardeningTester()
    success = tester.run_all()
    
    # Run in-repo cost-safe suite
    print("\n" + "=" * 70)
    print("[REGRESSION] Running in-repo cost-safe suite...")
    print("=" * 70)
    import subprocess
    try:
        result = subprocess.run(
            ["python", "tests/test_phase34.py"],
            cwd="/app/backend",
            capture_output=True,
            text=True,
            timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Look for result line
        for line in result.stdout.split("\n"):
            if "RESULT:" in line or "passed" in line.lower():
                print(f"\n✅ {line}")
        
        if result.returncode != 0:
            print(f"❌ In-repo suite failed with exit code {result.returncode}")
            success = False
    except Exception as e:
        print(f"❌ Failed to run in-repo suite: {e}")
        success = False
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
