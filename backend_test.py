"""Backend API tests for Khova AI — focus on status codes and basic flow validation."""
import requests
import sys
import time
from datetime import datetime

BASE_URL = "https://idea-to-asset.preview.emergentagent.com/api"

class KhovaAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.sample_project_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=120):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if self.session_token:
            req_headers['Authorization'] = f'Bearer {self.session_token}'
        if headers:
            req_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=req_headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.text[:200]}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root(self):
        """Test root endpoint"""
        success, response = self.run_test("Root endpoint", "GET", "", 200)
        return success

    def test_dev_login(self):
        """Test dev-login bypass"""
        success, response = self.run_test(
            "Dev Login",
            "POST",
            "auth/dev-login",
            200,
            data={"email": "tester@khova.ai", "name": "Tester"}
        )
        if success and 'session_token' in response:
            self.session_token = response['session_token']
            print(f"   Session token obtained: {self.session_token[:20]}...")
            return True
        return False

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        success, response = self.run_test("Auth Me", "GET", "auth/me", 200)
        if success and response.get('email') == 'tester@khova.ai':
            print(f"   User: {response.get('name')} ({response.get('email')})")
            return True
        return False

    def test_create_project(self):
        """Create a new project (anonymous)"""
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data={"title": "Test Project", "ui_language": "id", "product_language": "id"}
        )
        if success and 'id' in response:
            self.project_id = response['id']
            print(f"   Project ID: {self.project_id}")
            return True
        return False

    def test_get_project(self):
        """Get project details"""
        if not self.project_id:
            print("⚠️  Skipped - No project ID")
            return False
        success, response = self.run_test(
            "Get Project",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        return success

    def test_save_discover(self):
        """Save discover step (minimal data)"""
        if not self.project_id:
            print("⚠️  Skipped - No project ID")
            return False
        success, response = self.run_test(
            "Save Discover",
            "POST",
            f"projects/{self.project_id}/discover",
            200,
            data={
                "mode": "know",
                "idea": "Panduan produktivitas untuk freelancer",
                "expertise": "Manajemen waktu",
                "audience": "Freelancer pemula"
            }
        )
        return success

    def test_create_sample(self):
        """Create sample project (prefilled)"""
        success, response = self.run_test(
            "Create Sample Project",
            "POST",
            "projects/sample",
            200
        )
        if success and 'id' in response:
            self.sample_project_id = response['id']
            print(f"   Sample Project ID: {self.sample_project_id}")
            return True
        return False

    def test_list_projects(self):
        """List user projects (requires auth)"""
        success, response = self.run_test("List Projects", "GET", "projects", 200)
        if success:
            print(f"   Found {len(response)} projects")
        return success

    def test_settings(self):
        """Test settings endpoints"""
        success1, response1 = self.run_test("Get Settings", "GET", "settings", 200)
        success2, response2 = self.run_test(
            "Put Settings",
            "PUT",
            "settings",
            200,
            data={"ui_language": "en"}
        )
        return success1 and success2

    def test_config_models(self):
        """Test config/models endpoint"""
        success, response = self.run_test("Config Models", "GET", "config/models", 200)
        if success:
            print(f"   Providers: {list(response.get('providers', {}).keys())}")
        return success

    def test_format_selection(self):
        """Test format selection on sample project"""
        if not self.sample_project_id:
            print("⚠️  Skipped - No sample project")
            return False
        success, response = self.run_test(
            "Set Format (Spreadsheet)",
            "POST",
            f"projects/{self.sample_project_id}/format",
            200,
            data={"format": "spreadsheet"}
        )
        return success

    def test_spreadsheet_spec(self):
        """Test spreadsheet spec generation (auth-gated)"""
        if not self.sample_project_id:
            print("⚠️  Skipped - No sample project")
            return False
        # This is a generation endpoint, so it requires auth and may take time
        success, response = self.run_test(
            "Spreadsheet Spec",
            "POST",
            f"projects/{self.sample_project_id}/spreadsheet/spec",
            200,
            timeout=90
        )
        return success

    def test_spreadsheet_build(self):
        """Test spreadsheet build (auth-gated)"""
        if not self.sample_project_id:
            print("⚠️  Skipped - No sample project")
            return False
        success, response = self.run_test(
            "Spreadsheet Build",
            "POST",
            f"projects/{self.sample_project_id}/spreadsheet/build",
            200,
            timeout=30
        )
        if success and response.get('asset'):
            print(f"   Asset ID: {response['asset']['id']}")
        return success

def main():
    print("=" * 60)
    print("Khova AI Backend API Tests")
    print("=" * 60)
    
    tester = KhovaAPITester()
    
    # Basic tests
    print("\n--- BASIC ENDPOINTS ---")
    tester.test_root()
    tester.test_config_models()
    
    # Auth tests
    print("\n--- AUTHENTICATION ---")
    if not tester.test_dev_login():
        print("❌ Dev login failed, stopping tests")
        return 1
    tester.test_auth_me()
    
    # Settings
    print("\n--- SETTINGS ---")
    tester.test_settings()
    
    # Anonymous project flow
    print("\n--- ANONYMOUS PROJECT FLOW ---")
    tester.test_create_project()
    tester.test_get_project()
    tester.test_save_discover()
    
    # Sample project (prefilled for generation tests)
    print("\n--- SAMPLE PROJECT ---")
    tester.test_create_sample()
    tester.test_list_projects()
    
    # Auth-gated generation (using sample to avoid expensive research/opportunities)
    print("\n--- AUTH-GATED GENERATION (Sample Project) ---")
    tester.test_format_selection()
    tester.test_spreadsheet_spec()
    tester.test_spreadsheet_build()
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 60)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
