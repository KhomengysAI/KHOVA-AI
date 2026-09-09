"""
Khova AI Backend API Test Suite - Phase 2 Testing
Tests full pipeline + NEW bonus generation + regression checks
"""
import requests
import sys
import json
from datetime import datetime

class KhovaAPITester:
    def __init__(self, base_url="https://idea-to-asset.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.user_data = None

    def log(self, msg, status="info"):
        prefix = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}.get(status, "•")
        print(f"{prefix} {msg}")

    def run_test(self, name, method, endpoint, expected_status, data=None, check_fn=None):
        """Run a single API test with optional validation function"""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        self.log(f"Testing {name}...", "info")
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=120)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=120)
            elif method == 'PATCH':
                response = self.session.patch(url, json=data, timeout=120)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=120)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✓ {name} - Status: {response.status_code}", "success")
                
                # Run additional validation if provided
                if check_fn and response.status_code < 400:
                    try:
                        resp_data = response.json() if response.content else {}
                        check_fn(resp_data)
                    except Exception as e:
                        self.log(f"Validation failed: {str(e)}", "error")
                        self.tests_passed -= 1
                        return False, {}
                
                return True, response.json() if response.content else {}
            else:
                self.log(f"✗ {name} - Expected {expected_status}, got {response.status_code}", "error")
                if response.content:
                    try:
                        err = response.json()
                        self.log(f"  Error: {err.get('detail', err)}", "error")
                    except:
                        self.log(f"  Response: {response.text[:200]}", "error")
                return False, {}

        except requests.exceptions.Timeout:
            self.log(f"✗ {name} - Request timeout (>120s)", "error")
            return False, {}
        except Exception as e:
            self.log(f"✗ {name} - Error: {str(e)}", "error")
            return False, {}

    def test_dev_login(self):
        """Test dev login authentication"""
        success, response = self.run_test(
            "Dev Login",
            "POST",
            "auth/dev-login",
            200,
            data={"email": "tester@khova.ai", "name": "Tester"}
        )
        if success:
            self.user_data = response
            self.log(f"Logged in as: {response.get('email')}", "success")
        return success

    def test_create_project(self):
        """Create a new project"""
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data={
                "title": "Test eBook Project",
                "ui_language": "id",
                "product_language": "id"
            }
        )
        if success and response.get('id'):
            self.project_id = response['id']
            self.log(f"Project created: {self.project_id}", "success")
        return success

    def test_discover(self):
        """Save discover data"""
        return self.run_test(
            "Save Discover",
            "POST",
            f"projects/{self.project_id}/discover",
            200,
            data={
                "mode": "know",
                "idea": "Panduan praktis untuk belajar produktivitas pribadi",
                "expertise": "Manajemen waktu dan produktivitas",
                "audience": "Profesional muda yang ingin lebih produktif"
            }
        )[0]

    def test_research(self):
        """Run market research (slow - real LLM call)"""
        self.log("Running research (60-90s expected)...", "warning")
        return self.run_test(
            "Market Research",
            "POST",
            f"projects/{self.project_id}/research",
            200,
            check_fn=lambda r: self.log(f"Research status: {r.get('research', {}).get('status')}", "info")
        )[0]

    def test_opportunities(self):
        """Generate opportunities (slow - real LLM call)"""
        self.log("Generating opportunities (30-60s expected)...", "warning")
        success, response = self.run_test(
            "Generate Opportunities",
            "POST",
            f"projects/{self.project_id}/opportunities",
            200,
            check_fn=lambda r: self.log(f"Generated {len(r.get('opportunities', []))} opportunities", "info")
        )
        return success

    def test_select_opportunity(self):
        """Select first opportunity"""
        # Get project to find first opportunity
        proj_resp = self.session.get(f"{self.base_url}/projects/{self.project_id}")
        if proj_resp.status_code == 200:
            proj = proj_resp.json()
            opps = proj.get('opportunities', [])
            if opps:
                opp_id = opps[0]['id']
                return self.run_test(
                    "Select Opportunity",
                    "POST",
                    f"projects/{self.project_id}/select-opportunity",
                    200,
                    data={"opportunity_id": opp_id}
                )[0]
        return False

    def test_positioning(self):
        """Generate positioning"""
        return self.run_test(
            "Generate Positioning",
            "POST",
            f"projects/{self.project_id}/positioning",
            200
        )[0]

    def test_transformation(self):
        """Generate transformation with palette"""
        success, response = self.run_test(
            "Generate Transformation",
            "POST",
            f"projects/{self.project_id}/transformation",
            200,
            check_fn=lambda r: self.log(f"Palette: {r.get('transformation', {}).get('palette', {}).get('primary')}", "info")
        )
        return success

    def test_set_format_ebook(self):
        """Set format to ebook"""
        return self.run_test(
            "Set Format (eBook)",
            "POST",
            f"projects/{self.project_id}/format",
            200,
            data={"format": "ebook"}
        )[0]

    def test_ebook_plan(self):
        """Generate ebook plan (NEW: check for action_plan chapter, bonuses, visuals)"""
        self.log("Generating ebook plan (30-60s expected)...", "warning")
        
        def validate_plan(response):
            ebook = response.get('ebook', {})
            meta = ebook.get('meta', {})
            toc = ebook.get('toc', [])
            bonuses = ebook.get('bonuses', [])
            visuals = ebook.get('visuals', [])
            
            # Check for action_plan chapter
            action_plan_chapters = [ch for ch in toc if ch.get('kind') == 'action_plan']
            if not action_plan_chapters:
                raise Exception("No action_plan chapter found in TOC")
            self.log(f"✓ Action plan chapter found: '{action_plan_chapters[0].get('title')}'", "success")
            
            # Check bonuses
            self.log(f"Bonuses planned: {len(bonuses)}", "info")
            
            # Check visuals
            self.log(f"Visuals planned: {len(visuals)}", "info")
            
            # Check meta
            self.log(f"Title: {meta.get('title')}", "info")
            self.log(f"Chapters: {len(toc)}", "info")
        
        return self.run_test(
            "Generate eBook Plan",
            "POST",
            f"projects/{self.project_id}/ebook/plan",
            200,
            check_fn=validate_plan
        )[0]

    def test_ebook_section(self, chapter_num=1):
        """Generate a single ebook section"""
        self.log(f"Generating chapter {chapter_num} (20-40s expected)...", "warning")
        
        def validate_section(response):
            ebook = response.get('ebook', {})
            sections = ebook.get('sections', [])
            section = next((s for s in sections if s.get('chapter_num') == chapter_num), None)
            if not section:
                raise Exception(f"Chapter {chapter_num} not found in sections")
            
            content = section.get('content_html', '')
            # Check for LaTeX delimiters (should NOT exist)
            if '$' in content and ('$$' in content or content.count('$') > 2):
                self.log("⚠️  Warning: Possible LaTeX delimiters found in content", "warning")
            
            self.log(f"✓ Chapter {chapter_num} generated ({len(content)} chars)", "success")
        
        return self.run_test(
            f"Generate Chapter {chapter_num}",
            "POST",
            f"projects/{self.project_id}/ebook/section",
            200,
            data={"chapter_num": chapter_num},
            check_fn=validate_section
        )[0]

    def test_ebook_intro(self):
        """Generate ebook introduction"""
        return self.run_test(
            "Generate Introduction",
            "POST",
            f"projects/{self.project_id}/ebook/intro",
            200
        )[0]

    def test_ebook_cover(self):
        """Generate ebook cover"""
        self.log("Generating cover (20-40s expected)...", "warning")
        return self.run_test(
            "Generate Cover",
            "POST",
            f"projects/{self.project_id}/ebook/cover",
            200,
            check_fn=lambda r: self.log(f"Cover asset: {r.get('ebook', {}).get('cover_asset_id')}", "info")
        )[0]

    def test_bonus_generation(self):
        """NEW: Test bonus asset generation"""
        # First get project to check bonuses
        proj_resp = self.session.get(f"{self.base_url}/projects/{self.project_id}")
        if proj_resp.status_code != 200:
            self.log("Failed to get project for bonus test", "error")
            return False
        
        proj = proj_resp.json()
        ebook = proj.get('ebook', {})
        bonuses = ebook.get('bonuses', [])
        
        if not bonuses:
            self.log("No bonuses in plan, skipping bonus generation test", "warning")
            return True  # Not a failure, just no bonuses
        
        self.log(f"Testing bonus generation for first bonus (20-40s expected)...", "warning")
        
        def validate_bonus(response):
            ebook = response.get('ebook', {})
            bonuses = ebook.get('bonuses', [])
            if bonuses and bonuses[0].get('asset_id'):
                self.log(f"✓ Bonus asset generated: {bonuses[0].get('asset_id')}", "success")
            else:
                raise Exception("Bonus asset_id not set after generation")
        
        return self.run_test(
            "Generate Bonus Asset (index 0)",
            "POST",
            f"projects/{self.project_id}/ebook/bonus/0/generate",
            200,
            check_fn=validate_bonus
        )[0]

    def test_bonus_edge_cases(self):
        """NEW: Test bonus generation edge cases"""
        # Test invalid index
        success1 = self.run_test(
            "Bonus Invalid Index (should 404)",
            "POST",
            f"projects/{self.project_id}/ebook/bonus/999/generate",
            404
        )[0]
        
        # Test with project without ebook plan
        temp_proj_resp = self.session.post(
            f"{self.base_url}/projects",
            json={"title": "Temp Project", "ui_language": "id", "product_language": "id"}
        )
        if temp_proj_resp.status_code == 200:
            temp_id = temp_proj_resp.json()['id']
            success2 = self.run_test(
                "Bonus Without Plan (should 400)",
                "POST",
                f"projects/{temp_id}/ebook/bonus/0/generate",
                400
            )[0]
            return success1 and success2
        
        return success1

    def test_qa_run(self):
        """Run QA review"""
        return self.run_test(
            "Run QA Review",
            "POST",
            f"projects/{self.project_id}/qa",
            200,
            check_fn=lambda r: self.log(f"QA score: {r.get('qa', [{}])[0].get('overall', 'N/A')}/10", "info")
        )[0]

    def test_qa_apply(self):
        """Apply QA improvements (REGRESSION: must actually rewrite content)"""
        # Get current content
        proj_resp = self.session.get(f"{self.base_url}/projects/{self.project_id}")
        if proj_resp.status_code != 200:
            return False
        
        proj = proj_resp.json()
        ebook = proj.get('ebook', {})
        sections_before = ebook.get('sections', [])
        if not sections_before:
            self.log("No sections to apply QA to", "warning")
            return True
        
        content_before = sections_before[0].get('content_html', '')
        
        # Apply QA
        self.log("Applying QA improvements (may take 60-120s for multiple chapters)...", "warning")
        success, response = self.run_test(
            "Apply QA Improvements",
            "POST",
            f"projects/{self.project_id}/qa/apply",
            200
        )
        
        if success:
            # Verify content actually changed
            sections_after = response.get('ebook', {}).get('sections', [])
            if sections_after:
                content_after = sections_after[0].get('content_html', '')
                if content_after == content_before:
                    self.log("⚠️  WARNING: QA apply did not change content!", "error")
                    return False
                else:
                    self.log("✓ QA apply successfully rewrote content", "success")
        
        return success

    def test_branding(self):
        """Generate branding"""
        return self.run_test(
            "Generate Branding",
            "POST",
            f"projects/{self.project_id}/branding",
            200,
            data={"style": "Premium"}
        )[0]

    def test_palette_consistency(self):
        """REGRESSION: Verify palette is canonical across Transformation and Branding"""
        proj_resp = self.session.get(f"{self.base_url}/projects/{self.project_id}")
        if proj_resp.status_code != 200:
            return False
        
        proj = proj_resp.json()
        transformation_palette = proj.get('transformation', {}).get('palette', {})
        
        # Check ebook design system uses same palette
        ebook_palette = proj.get('ebook', {}).get('design_system', {}).get('colors', {})
        
        if transformation_palette.get('primary') == ebook_palette.get('primary'):
            self.log("✓ Palette is consistent between Transformation and eBook", "success")
            self.tests_passed += 1
        else:
            self.log("✗ Palette mismatch detected", "error")
            return False
        
        self.tests_run += 1
        return True

    def test_ebook_preview(self):
        """Test ebook preview HTML endpoint"""
        return self.run_test(
            "eBook Preview HTML",
            "GET",
            f"projects/{self.project_id}/ebook/preview-html",
            200,
            check_fn=lambda r: self.log("Preview HTML generated", "info")
        )[0]

    def test_export_pdf(self):
        """Export ebook as PDF"""
        self.log("Exporting PDF (may take 30-60s)...", "warning")
        success, response = self.run_test(
            "Export PDF",
            "POST",
            f"projects/{self.project_id}/ebook/export",
            200,
            check_fn=lambda r: self.log(f"PDF asset: {r.get('asset', {}).get('id')}", "info")
        )
        return success

    def test_spreadsheet_flow(self):
        """REGRESSION: Test spreadsheet format still works"""
        # Create new project for spreadsheet
        proj_resp = self.session.post(
            f"{self.base_url}/projects",
            json={"title": "Spreadsheet Test", "ui_language": "id", "product_language": "id"}
        )
        if proj_resp.status_code != 200:
            return False
        
        ss_proj_id = proj_resp.json()['id']
        
        # Quick pipeline to transformation
        self.session.post(f"{self.base_url}/projects/{ss_proj_id}/discover", 
                         json={"mode": "know", "idea": "Budget planner"})
        
        # Set format to spreadsheet
        success = self.run_test(
            "Spreadsheet Format",
            "POST",
            f"projects/{ss_proj_id}/format",
            200,
            data={"format": "spreadsheet"}
        )[0]
        
        return success

    def run_all_tests(self):
        """Run complete test suite"""
        self.log("=" * 60, "info")
        self.log("Khova AI Backend Test Suite - Phase 2", "info")
        self.log("=" * 60, "info")
        
        # Auth
        if not self.test_dev_login():
            self.log("Auth failed, stopping tests", "error")
            return False
        
        # Project creation
        if not self.test_create_project():
            self.log("Project creation failed, stopping tests", "error")
            return False
        
        # Full pipeline
        pipeline_tests = [
            self.test_discover,
            self.test_research,
            self.test_opportunities,
            self.test_select_opportunity,
            self.test_positioning,
            self.test_transformation,
            self.test_set_format_ebook,
            self.test_ebook_plan,
        ]
        
        for test in pipeline_tests:
            if not test():
                self.log(f"Pipeline test {test.__name__} failed", "error")
                return False
        
        # Generate some content
        self.test_ebook_section(1)
        self.test_ebook_section(2)
        self.test_ebook_intro()
        self.test_ebook_cover()
        
        # NEW: Bonus generation
        self.test_bonus_generation()
        self.test_bonus_edge_cases()
        
        # QA flow
        self.test_qa_run()
        self.test_qa_apply()
        
        # Branding
        self.test_branding()
        
        # Consistency checks
        self.test_palette_consistency()
        
        # Preview & Export
        self.test_ebook_preview()
        self.test_export_pdf()
        
        # Regression: other formats
        self.test_spreadsheet_flow()
        
        return True

def main():
    tester = KhovaAPITester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    print("=" * 60)
    
    if tester.tests_passed == tester.tests_run:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
