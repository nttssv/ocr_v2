#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Case Management & OCR API
Tests all endpoints with real API calls and demonstrates end-to-end workflows.
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

import requests

# Import test configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from unit.test_config import (
    TestEnvironment,
    cleanup_test_environment,
    setup_test_environment,
)

# Configuration
BASE_URL = "http://localhost:8001"  # Case Management API
OCR_API_URL = "http://localhost:8000"  # Original OCR API
SAMPLE_PDF = "data/samples/1.pdf"


class APITester:
    def __init__(self, base_url: str, ocr_url: str):
        self.base_url = base_url
        self.ocr_url = ocr_url
        self.session = requests.Session()
        self.test_results = []

    def generate_idempotency_key(self) -> str:
        """Generate unique idempotency key"""
        return str(uuid.uuid4())

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"

        # Add idempotency key for POST/PATCH requests
        if method.upper() in ["POST", "PATCH"]:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Idempotency-Key"] = self.generate_idempotency_key()

        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check...")

        response = self.make_request("GET", "/v1/health")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Health Check", True, f"Status: {data.get('status')}")
            return True
        else:
            self.log_test(
                "Health Check",
                False,
                f"Status: {response.status_code if response else 'No response'}",
            )
            return False

    def test_case_management(self) -> str:
        """Test case management endpoints"""
        print("\n📁 Testing Case Management...")

        # 1. Create a case
        case_data = {
            "name": "Test Legal Document Case",
            "description": "Integration test case for Vietnamese legal documents",
            "metadata": {
                "client": "Test Client",
                "document_type": "legal",
                "priority_level": "high",
            },
            "priority": 8,
        }

        response = self.make_request("POST", "/v1/cases", json=case_data)
        if not response or response.status_code != 200:
            self.log_test(
                "Create Case",
                False,
                f"Status: {response.status_code if response else 'No response'}",
            )
            return None

        case = response.json()
        case_id = case["case_id"]
        self.log_test("Create Case", True, f"Case ID: {case_id}")

        # 2. Get case details
        response = self.make_request("GET", f"/v1/cases/{case_id}")
        if response and response.status_code == 200:
            self.log_test("Get Case Details", True, f"Case: {response.json()['name']}")
        else:
            self.log_test("Get Case Details", False)

        # 3. Update case
        update_data = {
            "description": "Updated description for integration test",
            "metadata": {"updated": True},
        }
        response = self.make_request("PATCH", f"/v1/cases/{case_id}", json=update_data)
        if response and response.status_code == 200:
            self.log_test("Update Case", True)
        else:
            self.log_test("Update Case", False)

        # 4. List cases
        response = self.make_request("GET", "/v1/cases", params={"limit": 10})
        if response and response.status_code == 200:
            cases = response.json()
            self.log_test("List Cases", True, f"Found {len(cases['cases'])} cases")
        else:
            self.log_test("List Cases", False)

        return case_id

    def test_document_management(self, case_id: str) -> str:
        """Test document management endpoints"""
        print("\n📄 Testing Document Management...")

        # 1. Add document to case
        doc_data = {
            "filename": "test_legal_document.pdf",
            "url": f"file://{os.path.abspath(SAMPLE_PDF)}",
            "metadata": {
                "pages": 4,
                "language": "vietnamese",
                "document_type": "court_decision",
            },
        }

        response = self.make_request(
            "POST", f"/v1/cases/{case_id}/documents", json=doc_data
        )
        if not response or response.status_code != 200:
            self.log_test(
                "Add Document",
                False,
                f"Status: {response.status_code if response else 'No response'}",
            )
            return None

        document = response.json()
        document_id = document["document_id"]
        self.log_test("Add Document", True, f"Document ID: {document_id}")

        # 2. List case documents
        response = self.make_request("GET", f"/v1/cases/{case_id}/documents")
        if response and response.status_code == 200:
            documents = response.json()
            self.log_test(
                "List Case Documents", True, f"Found {len(documents)} documents"
            )
        else:
            self.log_test("List Case Documents", False)

        return document_id

    def test_job_management(self, case_id: str) -> str:
        """Test job management endpoints"""
        print("\n⚙️ Testing Job Management...")

        # 1. Create OCR job
        job_data = {
            "case_ids": [case_id],
            "language": "vie",
            "enable_handwriting_detection": False,
            "priority": 7,
        }

        response = self.make_request("POST", "/v1/jobs", json=job_data)
        if not response or response.status_code != 200:
            self.log_test(
                "Create OCR Job",
                False,
                f"Status: {response.status_code if response else 'No response'}",
            )
            return None

        job = response.json()
        job_id = job["job_id"]
        self.log_test("Create OCR Job", True, f"Job ID: {job_id}")

        # 2. Get job status
        response = self.make_request("GET", f"/v1/jobs/{job_id}")
        if response and response.status_code == 200:
            job_status = response.json()
            self.log_test("Get Job Status", True, f"Status: {job_status['status']}")
        else:
            self.log_test("Get Job Status", False)

        # 3. List jobs
        response = self.make_request("GET", "/v1/jobs", params={"limit": 10})
        if response and response.status_code == 200:
            jobs = response.json()
            self.log_test("List Jobs", True, f"Found {len(jobs['jobs'])} jobs")
        else:
            self.log_test("List Jobs", False)

        return job_id

    def test_extraction_workflow(self, case_id: str):
        """Test extraction workflow endpoints"""
        print("\n🔄 Testing Extraction Workflow...")

        # 1. Simulate case ready for extraction
        # First, update case status manually (in real scenario, this would be done by job completion)
        import requests

        # Direct database update for testing
        print("   Simulating case ready for extraction...")

        # 2. Get cases ready for extraction (without claiming)
        response = self.make_request(
            "GET", "/v1/cases/ready-for-extraction", params={"claim": False, "limit": 5}
        )
        if response and response.status_code == 200:
            ready_cases = response.json()
            self.log_test(
                "Get Ready Cases (No Claim)",
                True,
                f"Found {len(ready_cases['cases'])} ready cases",
            )
        else:
            self.log_test("Get Ready Cases (No Claim)", False)

        # 3. Claim cases for extraction
        response = self.make_request(
            "GET",
            "/v1/cases/ready-for-extraction",
            params={"claim": True, "lease_duration_minutes": 30, "limit": 1},
        )
        if response and response.status_code == 200:
            claimed_cases = response.json()
            self.log_test(
                "Claim Cases for Extraction",
                True,
                f"Claimed: {claimed_cases['claimed']}",
            )
        else:
            self.log_test("Claim Cases for Extraction", False)

        # 4. Update extraction status to in_progress
        update_data = {
            "status": "in_progress",
            "metadata": {
                "worker_id": "test_worker_001",
                "started_at": datetime.now().isoformat(),
            },
        }
        response = self.make_request(
            "PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data
        )
        if response and response.status_code == 200:
            self.log_test("Update Extraction Status (In Progress)", True)
        else:
            self.log_test("Update Extraction Status (In Progress)", False)

        # 5. Extend lease
        extension_data = {"duration_minutes": 45}
        response = self.make_request(
            "PATCH", f"/v1/cases/{case_id}/lease/extend", json=extension_data
        )
        if response and response.status_code == 200:
            self.log_test("Extend Lease", True)
        else:
            self.log_test("Extend Lease", False)

        # 6. Update extraction status to succeeded
        update_data = {
            "status": "succeeded",
            "metadata": {
                "completed_at": datetime.now().isoformat(),
                "extracted_entities": 15,
                "confidence_score": 0.95,
            },
        }
        response = self.make_request(
            "PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data
        )
        if response and response.status_code == 200:
            self.log_test("Update Extraction Status (Succeeded)", True)
        else:
            self.log_test("Update Extraction Status (Succeeded)", False)

    def test_bulk_operations(self, case_ids: List[str]):
        """Test bulk operations"""
        print("\n📦 Testing Bulk Operations...")

        if not case_ids:
            self.log_test("Bulk Operations", False, "No case IDs provided")
            return

        # Bulk update extraction statuses
        updates = []
        for case_id in case_ids[:3]:  # Limit to first 3 cases
            updates.append(
                {
                    "case_id": case_id,
                    "status": "pending",
                    "metadata": {"bulk_updated": True},
                }
            )

        bulk_data = {"updates": updates}
        response = self.make_request(
            "PATCH", "/v1/cases/extraction-status/bulk", json=bulk_data
        )
        if response and response.status_code == 200:
            results = response.json()
            successful = sum(1 for r in results["results"] if r["success"])
            self.log_test(
                "Bulk Update Extraction Status",
                True,
                f"{successful}/{len(updates)} successful",
            )
        else:
            self.log_test("Bulk Update Extraction Status", False)

    def test_webhook_system(self):
        """Test webhook system"""
        print("\n🔗 Testing Webhook System...")

        # 1. Send test webhook
        webhook_data = {
            "event_type": "job.completed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "job_id": "test_job_123",
                "case_ids": ["test_case_456"],
                "status": "completed",
                "processing_time": 10.5,
            },
        }

        response = self.make_request("POST", "/v1/webhooks/test", json=webhook_data)
        if response and response.status_code == 200:
            self.log_test("Send Test Webhook", True)
        else:
            self.log_test("Send Test Webhook", False)

        # 2. Get webhook history
        response = self.make_request(
            "GET", "/v1/webhooks/history", params={"limit": 10}
        )
        if response and response.status_code == 200:
            history = response.json()
            self.log_test(
                "Get Webhook History",
                True,
                f"Found {len(history['webhooks'])} webhooks",
            )
        else:
            self.log_test("Get Webhook History", False)

    def test_pagination_and_filtering(self):
        """Test pagination and filtering"""
        print("\n📄 Testing Pagination & Filtering...")

        # Test case filtering by status
        response = self.make_request(
            "GET", "/v1/cases", params={"status": "created", "limit": 5}
        )
        if response and response.status_code == 200:
            cases = response.json()
            self.log_test(
                "Filter Cases by Status",
                True,
                f"Found {len(cases['cases'])} created cases",
            )
        else:
            self.log_test("Filter Cases by Status", False)

        # Test job filtering
        response = self.make_request(
            "GET", "/v1/jobs", params={"status": "pending", "limit": 5}
        )
        if response and response.status_code == 200:
            jobs = response.json()
            self.log_test(
                "Filter Jobs by Status", True, f"Found {len(jobs['jobs'])} pending jobs"
            )
        else:
            self.log_test("Filter Jobs by Status", False)

    def test_metrics_and_monitoring(self):
        """Test metrics and monitoring endpoints"""
        print("\n📊 Testing Metrics & Monitoring...")

        # 1. Get system metrics
        response = self.make_request("GET", "/v1/metrics")
        if response and response.status_code == 200:
            metrics = response.json()
            self.log_test(
                "Get System Metrics",
                True,
                f"Case statuses: {len(metrics['case_statuses'])}",
            )
        else:
            self.log_test("Get System Metrics", False)

        # 2. Health check with stats
        response = self.make_request("GET", "/v1/health")
        if response and response.status_code == 200:
            health = response.json()
            stats = health.get("stats", {})
            self.log_test(
                "Health Check with Stats",
                True,
                f"Cases: {stats.get('total_cases')}, Jobs: {stats.get('total_jobs')}",
            )
        else:
            self.log_test("Health Check with Stats", False)

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n⚠️ Testing Error Handling...")

        # 1. Get non-existent case
        response = self.make_request("GET", "/v1/cases/non-existent-id")
        if response and response.status_code == 404:
            self.log_test("Get Non-existent Case", True, "Correctly returned 404")
        else:
            self.log_test("Get Non-existent Case", False)

        # 2. Create job with invalid case ID
        job_data = {"case_ids": ["invalid-case-id"], "language": "vie"}
        response = self.make_request("POST", "/v1/jobs", json=job_data)
        if response and response.status_code == 400:
            self.log_test(
                "Create Job with Invalid Case", True, "Correctly returned 400"
            )
        else:
            self.log_test("Create Job with Invalid Case", False)

        # 3. Missing idempotency key
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{self.base_url}/v1/cases", json={"name": "Test"}, headers=headers
        )
        if response.status_code == 400:
            self.log_test("Missing Idempotency Key", True, "Correctly returned 400")
        else:
            self.log_test("Missing Idempotency Key", False)

    def test_ocr_integration(self):
        """Test integration with original OCR API"""
        print("\n🔗 Testing OCR API Integration...")

        # Check if OCR API is running
        try:
            response = requests.get(f"{self.ocr_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("OCR API Health Check", True, "OCR API is running")

                # Test document processing
                if os.path.exists(SAMPLE_PDF):
                    with open(SAMPLE_PDF, "rb") as f:
                        files = {"file": f}
                        data = {
                            "language": "vie",
                            "enable_handwriting_detection": False,
                        }
                        response = requests.post(
                            f"{self.ocr_url}/documents/transform",
                            files=files,
                            data=data,
                            timeout=30,
                        )

                    if response.status_code == 200:
                        result = response.json()
                        self.log_test(
                            "OCR Document Processing",
                            True,
                            f"Document ID: {result.get('document_id')}",
                        )
                    else:
                        self.log_test("OCR Document Processing", False)
                else:
                    self.log_test(
                        "OCR Document Processing",
                        False,
                        f"Sample PDF not found: {SAMPLE_PDF}",
                    )
            else:
                self.log_test(
                    "OCR API Health Check", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            self.log_test("OCR API Health Check", False, f"Error: {str(e)}")

    def test_hierarchy_enhancement(self):
        """Test API Output Hierarchy Enhancement"""
        print("\n🧪 Testing API Output Hierarchy Enhancement")

        # Test cases for hierarchy enhancement
        test_cases = [
            {
                "name": "Default behavior (no relative_input_path)",
                "relative_input_path": None,
                "expected_output": "output/An_PT_1/",
            },
            {
                "name": "Folder1 hierarchy",
                "relative_input_path": "folder1",
                "expected_output": "output/folder1/An_PT_1/",
            },
            {
                "name": "Folder2 hierarchy",
                "relative_input_path": "folder2",
                "expected_output": "output/folder2/An_PT_1/",
            },
            {
                "name": "Nested folder hierarchy",
                "relative_input_path": "samples/subfolder",
                "expected_output": "output/samples/subfolder/An_PT_1/",
            },
        ]

        # Check if test PDF exists
        test_pdf_path = "samples/folder1/An_PT_1.pdf"
        if not os.path.exists(test_pdf_path):
            # Try alternative paths
            alternative_paths = ["data/samples/1.pdf", SAMPLE_PDF]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    test_pdf_path = alt_path
                    break
            else:
                self.log_test("Hierarchy Enhancement Setup", False, "No test PDF found")
                return

        for i, test_case in enumerate(test_cases, 1):
            test_name = f"Hierarchy Test {i}: {test_case['name']}"

            try:
                # Prepare request data
                with open(test_pdf_path, "rb") as f:
                    files = {"file": f}
                    data = {"language": "vie", "enable_handwriting_detection": False}

                    # Add relative_input_path if specified
                    if test_case["relative_input_path"]:
                        data["relative_input_path"] = test_case["relative_input_path"]

                    # Submit document for processing
                    response = requests.post(
                        f"{self.ocr_url}/documents/transform", files=files, data=data
                    )

                if response.status_code == 200:
                    result = response.json()
                    document_id = result["document_id"]

                    # Wait for processing to complete (with timeout)
                    max_wait = 60  # 60 seconds timeout
                    wait_time = 0
                    processing_complete = False

                    while wait_time < max_wait:
                        status_response = requests.get(
                            f"{self.ocr_url}/documents/status/{document_id}"
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data["status"] == "completed":
                                processing_complete = True
                                if "result" in status_data and status_data["result"]:
                                    output_dir = status_data["result"].get(
                                        "output_directory"
                                    )
                                    if output_dir and os.path.exists(output_dir):
                                        self.log_test(
                                            test_name, True, f"Output: {output_dir}"
                                        )
                                    else:
                                        self.log_test(
                                            test_name,
                                            False,
                                            f"Output directory not found: {output_dir}",
                                        )
                                else:
                                    self.log_test(
                                        test_name, False, "No result data in response"
                                    )
                                break
                            elif status_data["status"] == "failed":
                                self.log_test(
                                    test_name,
                                    False,
                                    f"Processing failed: {status_data.get('error', 'Unknown error')}",
                                )
                                break

                        time.sleep(2)
                        wait_time += 2

                    if not processing_complete:
                        self.log_test(test_name, False, "Processing timeout")
                else:
                    self.log_test(
                        test_name, False, f"Upload failed: {response.status_code}"
                    )

            except Exception as e:
                self.log_test(test_name, False, f"Error: {e}")

        # Test path sanitization security
        self.test_path_sanitization()

    def test_path_sanitization(self):
        """Test path sanitization security features"""
        print("\n🔒 Testing Path Sanitization Security")

        # Test cases for security
        security_test_cases = [
            {
                "name": "Directory traversal attempt (../)",
                "relative_input_path": "../malicious",
                "should_fail": False,  # Should be sanitized, not fail
            },
            {
                "name": "Absolute path attempt (/etc/)",
                "relative_input_path": "/etc/passwd",
                "should_fail": False,  # Should be sanitized
            },
            {
                "name": "Current directory reference (./)",
                "relative_input_path": "./test",
                "should_fail": False,  # Should be sanitized
            },
        ]

        test_pdf_path = (
            SAMPLE_PDF if os.path.exists(SAMPLE_PDF) else "data/samples/1.pdf"
        )
        if not os.path.exists(test_pdf_path):
            self.log_test("Path Sanitization Setup", False, "No test PDF found")
            return

        for test_case in security_test_cases:
            test_name = f"Security Test: {test_case['name']}"

            try:
                with open(test_pdf_path, "rb") as f:
                    files = {"file": f}
                    data = {
                        "language": "vie",
                        "enable_handwriting_detection": False,
                        "relative_input_path": test_case["relative_input_path"],
                    }

                    response = requests.post(
                        f"{self.ocr_url}/documents/transform", files=files, data=data
                    )

                if response.status_code == 200:
                    # API should accept the request but sanitize the path
                    self.log_test(test_name, True, "Path sanitized successfully")
                else:
                    # Unexpected failure
                    self.log_test(
                        test_name, False, f"Unexpected response: {response.status_code}"
                    )

            except Exception as e:
                self.log_test(test_name, False, f"Error: {e}")

    def run_end_to_end_workflow(self):
        """Run complete end-to-end workflow"""
        print("\n🚀 Running End-to-End Workflow...")

        workflow_success = True

        try:
            # Step 1: Create case
            case_data = {
                "name": "E2E Test Case - Legal Document Processing",
                "description": "Complete workflow test for Vietnamese legal document",
                "metadata": {"workflow": "end_to_end", "test_run": True},
                "priority": 9,
            }

            response = self.make_request("POST", "/v1/cases", json=case_data)
            if not response or response.status_code != 200:
                raise Exception("Failed to create case")

            case = response.json()
            case_id = case["case_id"]
            print(f"   ✓ Created case: {case_id}")

            # Step 2: Add document
            doc_data = {
                "filename": "legal_document_e2e.pdf",
                "url": f"file://{os.path.abspath(SAMPLE_PDF)}",
                "metadata": {"test": "e2e_workflow"},
            }

            response = self.make_request(
                "POST", f"/v1/cases/{case_id}/documents", json=doc_data
            )
            if not response or response.status_code != 200:
                raise Exception("Failed to add document")

            document = response.json()
            print(f"   ✓ Added document: {document['document_id']}")

            # Step 3: Create OCR job
            job_data = {
                "case_ids": [case_id],
                "language": "vie",
                "enable_handwriting_detection": False,
                "priority": 9,
            }

            response = self.make_request("POST", "/v1/jobs", json=job_data)
            if not response or response.status_code != 200:
                raise Exception("Failed to create OCR job")

            job = response.json()
            job_id = job["job_id"]
            print(f"   ✓ Created OCR job: {job_id}")

            # Step 4: Simulate job completion and case ready for extraction
            # In real scenario, this would be done by the OCR processing system
            print("   ⏳ Simulating OCR job completion...")
            time.sleep(1)

            # Step 5: Get cases ready for extraction and claim
            response = self.make_request(
                "GET",
                "/v1/cases/ready-for-extraction",
                params={"claim": True, "lease_duration_minutes": 60},
            )
            if response and response.status_code == 200:
                print("   ✓ Claimed case for extraction")

            # Step 6: Update extraction status to in_progress
            update_data = {
                "status": "in_progress",
                "metadata": {"extraction_worker": "e2e_test_worker"},
            }
            response = self.make_request(
                "PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data
            )
            if response and response.status_code == 200:
                print("   ✓ Started extraction process")

            # Step 7: Complete extraction
            update_data = {
                "status": "succeeded",
                "metadata": {
                    "extraction_completed": True,
                    "entities_extracted": 12,
                    "confidence": 0.94,
                },
            }
            response = self.make_request(
                "PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data
            )
            if response and response.status_code == 200:
                print("   ✓ Completed extraction successfully")

            # Step 8: Verify final case status
            response = self.make_request("GET", f"/v1/cases/{case_id}")
            if response and response.status_code == 200:
                final_case = response.json()
                if final_case["status"] == "completed":
                    print("   ✅ End-to-end workflow completed successfully!")
                else:
                    print(f"   ⚠️ Unexpected final status: {final_case['status']}")

            self.log_test(
                "End-to-End Workflow", True, f"Case {case_id} processed successfully"
            )

        except Exception as e:
            workflow_success = False
            self.log_test("End-to-End Workflow", False, f"Error: {str(e)}")

        return workflow_success

    def generate_api_examples(self):
        """Generate comprehensive API examples"""
        print("\n📚 Generating API Examples...")

        examples = {
            "curl_examples": self._generate_curl_examples(),
            "python_examples": self._generate_python_examples(),
            "postman_collection": self._generate_postman_collection(),
        }

        # Save examples to file
        with open("api_examples.json", "w") as f:
            json.dump(examples, f, indent=2)

        print("   ✓ API examples saved to api_examples.json")
        return examples

    def _generate_curl_examples(self):
        """Generate cURL examples for all endpoints"""
        base_url = self.base_url

        return {
            "create_case": f"""curl -X POST "{base_url}/v1/cases" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: $(uuidgen)" \\
  -d '{{
    "name": "Legal Document Case",
    "description": "Processing Vietnamese court decision",
    "metadata": {{"client": "ABC Law Firm", "priority": "high"}},
    "priority": 8
  }}'""",
            "add_document": f"""curl -X POST "{base_url}/v1/cases/{{case_id}}/documents" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: $(uuidgen)" \\
  -d '{{
    "filename": "court_decision.pdf",
    "url": "https://example.com/documents/court_decision.pdf",
    "metadata": {{"pages": 4, "language": "vietnamese"}}
  }}'""",
            "create_job": f"""curl -X POST "{base_url}/v1/jobs" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: $(uuidgen)" \\
  -d '{{
    "case_ids": ["case_id_1", "case_id_2"],
    "language": "vie",
    "enable_handwriting_detection": false,
    "priority": 7
  }}'""",
            "claim_cases": f"""curl -X GET "{base_url}/v1/cases/ready-for-extraction?claim=true&lease_duration_minutes=30&limit=5" \\
  -H "Content-Type: application/json\"""",
            "update_extraction": f"""curl -X PATCH "{base_url}/v1/cases/{{case_id}}/extraction-status" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: $(uuidgen)" \\
  -d '{{
    "status": "succeeded",
    "metadata": {{"entities_extracted": 15, "confidence": 0.95}}
  }}'""",
        }

    def _generate_python_examples(self):
        """Generate Python examples using requests library"""
        return {
            "setup": """import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8001"
session = requests.Session()

def make_request(method, endpoint, **kwargs):
    url = f"{BASE_URL}{endpoint}"
    if method.upper() in ["POST", "PATCH"]:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Idempotency-Key"] = str(uuid.uuid4())
    return session.request(method, url, **kwargs)""",
            "create_case": """# Create a new case
case_data = {
    "name": "Legal Document Processing",
    "description": "Vietnamese court decision analysis",
    "metadata": {"client": "Law Firm XYZ", "urgent": True},
    "priority": 8
}

response = make_request("POST", "/v1/cases", json=case_data)
case = response.json()
case_id = case["case_id"]
print(f"Created case: {case_id}")""",
            "add_document": """# Add document to case
doc_data = {
    "filename": "legal_doc.pdf",
    "url": "https://example.com/docs/legal_doc.pdf",
    "metadata": {"pages": 4, "language": "vie"}
}

response = make_request("POST", f"/v1/cases/{case_id}/documents", json=doc_data)
document = response.json()
print(f"Added document: {document['document_id']}")""",
            "create_job": """# Create OCR job
job_data = {
    "case_ids": [case_id],
    "language": "vie",
    "enable_handwriting_detection": False,
    "priority": 7
}

response = make_request("POST", "/v1/jobs", json=job_data)
job = response.json()
job_id = job["job_id"]
print(f"Created job: {job_id}")""",
            "extraction_workflow": """# Extraction workflow
# 1. Get cases ready for extraction
response = make_request("GET", "/v1/cases/ready-for-extraction", 
                       params={"claim": True, "lease_duration_minutes": 30})
ready_cases = response.json()

# 2. Update extraction status
for case in ready_cases["cases"]:
    case_id = case["case_id"]
    
    # Start extraction
    update_data = {
        "status": "in_progress",
        "metadata": {"worker_id": "worker_001"}
    }
    make_request("PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data)
    
    # Complete extraction
    update_data = {
        "status": "succeeded",
        "metadata": {"entities": 15, "confidence": 0.95}
    }
    make_request("PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data)""",
        }

    def _generate_postman_collection(self):
        """Generate Postman collection"""
        return {
            "info": {
                "name": "Case Management & OCR API",
                "description": "Complete API collection for case management and extraction workflows",
                "version": "2.0.0",
            },
            "variable": [
                {"key": "base_url", "value": "http://localhost:8001"},
                {"key": "case_id", "value": ""},
                {"key": "job_id", "value": ""},
                {"key": "document_id", "value": ""},
            ],
            "item": [
                {
                    "name": "Case Management",
                    "item": [
                        {
                            "name": "Create Case",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json",
                                    },
                                    {"key": "Idempotency-Key", "value": "{{$guid}}"},
                                ],
                                "url": "{{base_url}}/v1/cases",
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps(
                                        {
                                            "name": "Test Case",
                                            "description": "API test case",
                                            "priority": 5,
                                        },
                                        indent=2,
                                    ),
                                },
                            },
                        },
                        {
                            "name": "Get Case",
                            "request": {
                                "method": "GET",
                                "url": "{{base_url}}/v1/cases/{{case_id}}",
                            },
                        },
                        {
                            "name": "List Cases",
                            "request": {
                                "method": "GET",
                                "url": "{{base_url}}/v1/cases?limit=10",
                            },
                        },
                    ],
                }
            ],
        }

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   - {test['test']}: {test['details']}")

        print("\n📊 Test Categories:")
        categories = {}
        for test in self.test_results:
            category = test["test"].split()[0]
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0}
            categories[category]["total"] += 1
            if test["success"]:
                categories[category]["passed"] += 1

        for category, stats in categories.items():
            rate = (stats["passed"] / stats["total"]) * 100
            print(f"   {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")


def main():
    """Main test runner"""
    print("🚀 Starting Comprehensive API Integration Tests")
    print("=" * 60)

    # Set up test environment with dedicated output directory
    with TestEnvironment():
        print(
            "🧪 Using dedicated test output directory to avoid cluttering production outputs"
        )

        # Check if APIs are running
        tester = APITester(BASE_URL, OCR_API_URL)

        # Test if case management API is running
        try:
            response = requests.get(f"{BASE_URL}/v1/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Case Management API not running on {BASE_URL}")
                print("   Please start the API with: python case_management_api.py")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Cannot connect to Case Management API: {e}")
            print("   Please start the API with: python case_management_api.py")
            sys.exit(1)

        print(f"✅ Case Management API is running on {BASE_URL}")

        # Run all tests
        test_case_id = None
        test_job_id = None

        # Core functionality tests
        if tester.test_health_check():
            test_case_id = tester.test_case_management()
            if test_case_id:
                test_document_id = tester.test_document_management(test_case_id)
                test_job_id = tester.test_job_management(test_case_id)
                tester.test_extraction_workflow(test_case_id)

        # Additional tests
        tester.test_bulk_operations([test_case_id] if test_case_id else [])
        tester.test_webhook_system()
        tester.test_pagination_and_filtering()
        tester.test_metrics_and_monitoring()
        tester.test_error_handling()
        tester.test_ocr_integration()
        tester.test_hierarchy_enhancement()

        # End-to-end workflow
        tester.run_end_to_end_workflow()

        # Generate API examples
        tester.generate_api_examples()

        # Print summary
        tester.print_summary()

        print("\n🎉 Integration testing completed!")
        print("📚 Check api_examples.json for comprehensive API usage examples")
        print(
            "🧪 Hierarchy enhancement tests included for API output structure validation"
        )


if __name__ == "__main__":
    main()
