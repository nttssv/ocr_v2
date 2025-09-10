#!/usr/bin/env python3
"""
OCR API Integration Test Suite

This script performs comprehensive integration tests on the OCR API to verify:
- API health and availability
- Document processing functionality
- Error handling
- Performance metrics
- Output validation
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCRAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed"] += 1
            logger.info(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            logger.error(f"❌ {test_name}: FAILED {message}")
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_api_info(self) -> bool:
        """Test API info endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["message", "version", "endpoints"]
                if all(key in data for key in expected_keys):
                    self.log_test("API Info Endpoint", True, f"Version: {data.get('version')}")
                    return True
                else:
                    self.log_test("API Info Endpoint", False, "Missing expected keys")
                    return False
            else:
                self.log_test("API Info Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Info Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_document_upload(self, file_path: str) -> Optional[str]:
        """Test document upload and processing"""
        try:
            if not os.path.exists(file_path):
                self.log_test("Document Upload", False, f"File not found: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'language': 'vie',
                    'enable_handwriting_detection': 'false'
                }
                
                response = self.session.post(
                    f"{self.base_url}/documents/transform",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                document_id = result.get('document_id')
                if document_id:
                    self.log_test("Document Upload", True, f"Document ID: {document_id}")
                    return document_id
                else:
                    self.log_test("Document Upload", False, "No document ID returned")
                    return None
            else:
                self.log_test("Document Upload", False, f"Status code: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test("Document Upload", False, f"Exception: {str(e)}")
            return None
    
    def test_document_status(self, document_id: str) -> bool:
        """Test document status checking"""
        try:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_keys = ["task_id", "status", "progress", "created_at", "updated_at"]
                if all(key in data for key in required_keys):
                    self.log_test("Document Status Check", True, f"Status: {data.get('status')}, Progress: {data.get('progress')}")
                    return True
                else:
                    self.log_test("Document Status Check", False, "Missing required keys")
                    return False
            else:
                self.log_test("Document Status Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Document Status Check", False, f"Exception: {str(e)}")
            return False
    
    def wait_for_completion(self, document_id: str, max_wait: int = 300) -> bool:
        """Wait for document processing to complete"""
        start_time = time.time()
        logger.info(f"Waiting for document {document_id} to complete processing...")
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(f"{self.base_url}/documents/status/{document_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    progress = data.get('progress', 0)
                    
                    logger.info(f"Status: {status}, Progress: {progress:.2f}")
                    
                    if status == "completed":
                        self.log_test("Document Processing Completion", True, f"Completed in {time.time() - start_time:.2f}s")
                        return True
                    elif status == "failed":
                        error = data.get('error', 'Unknown error')
                        self.log_test("Document Processing Completion", False, f"Processing failed: {error}")
                        return False
                    
                    time.sleep(5)  # Wait 5 seconds before checking again
                else:
                    self.log_test("Document Processing Completion", False, f"Status check failed: {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Document Processing Completion", False, f"Exception: {str(e)}")
                return False
        
        self.log_test("Document Processing Completion", False, f"Timeout after {max_wait}s")
        return False
    
    def test_processing_results(self, document_id: str) -> bool:
        """Test processing results validation"""
        try:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                
                if result:
                    # Check required fields
                    required_fields = ["document_id", "status", "total_pages", "pages"]
                    if all(field in result for field in required_fields):
                        pages = result.get('pages', [])
                        if pages:
                            # Check page structure
                            first_page = pages[0]
                            page_fields = ["page_number", "pdf_file", "text_file", "extracted_text"]
                            if all(field in first_page for field in page_fields):
                                self.log_test("Processing Results Validation", True, 
                                    f"Pages: {len(pages)}, Processing time: {result.get('processing_time', 'N/A')}s")
                                return True
                            else:
                                self.log_test("Processing Results Validation", False, "Invalid page structure")
                                return False
                        else:
                            self.log_test("Processing Results Validation", False, "No pages in result")
                            return False
                    else:
                        self.log_test("Processing Results Validation", False, "Missing required result fields")
                        return False
                else:
                    self.log_test("Processing Results Validation", False, "No result data")
                    return False
            else:
                self.log_test("Processing Results Validation", False, f"Status check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Processing Results Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_output_files(self, document_id: str) -> bool:
        """Test output files generation"""
        try:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                
                if result:
                    output_dir = result.get('output_directory')
                    if output_dir and os.path.exists(output_dir):
                        # Check for expected files
                        pdf_dir = os.path.join(output_dir, "pdf")
                        text_dir = os.path.join(output_dir, "text")
                        
                        if os.path.exists(pdf_dir) and os.path.exists(text_dir):
                            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
                            text_files = [f for f in os.listdir(text_dir) if f.endswith('.txt')]
                            
                            if pdf_files and text_files:
                                self.log_test("Output Files Generation", True, 
                                    f"PDF files: {len(pdf_files)}, Text files: {len(text_files)}")
                                return True
                            else:
                                self.log_test("Output Files Generation", False, "No PDF or text files found")
                                return False
                        else:
                            self.log_test("Output Files Generation", False, "Missing pdf or text directories")
                            return False
                    else:
                        self.log_test("Output Files Generation", False, f"Output directory not found: {output_dir}")
                        return False
                else:
                    self.log_test("Output Files Generation", False, "No result data for file validation")
                    return False
            else:
                self.log_test("Output Files Generation", False, f"Status check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Output Files Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test API error handling"""
        try:
            # Test with invalid file
            files = {'file': ('invalid.txt', b'not a pdf', 'text/plain')}
            data = {'language': 'vie'}
            
            response = self.session.post(
                f"{self.base_url}/documents/transform",
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Error Handling", True, "Correctly rejected invalid file type")
                return True
            else:
                self.log_test("Error Handling", False, f"Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False
    
    def test_performance_metrics(self, document_id: str) -> bool:
        """Test performance metrics"""
        try:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                
                if result:
                    processing_time = result.get('processing_time')
                    total_pages = result.get('total_pages', 0)
                    
                    if processing_time and total_pages > 0:
                        pages_per_second = total_pages / processing_time
                        self.log_test("Performance Metrics", True, 
                            f"Processing time: {processing_time:.2f}s, Pages: {total_pages}, Rate: {pages_per_second:.2f} pages/s")
                        return True
                    else:
                        self.log_test("Performance Metrics", False, "Missing processing time or page count")
                        return False
                else:
                    self.log_test("Performance Metrics", False, "No result data for performance metrics")
                    return False
            else:
                self.log_test("Performance Metrics", False, f"Status check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Performance Metrics", False, f"Exception: {str(e)}")
            return False
    
    def run_full_integration_test(self, test_file: str = "samples/1.pdf") -> Dict[str, Any]:
        """Run complete integration test suite"""
        logger.info("🚀 Starting OCR API Integration Test Suite")
        logger.info("=" * 50)
        
        # Test 1: API Health
        if not self.test_api_health():
            logger.error("❌ API is not healthy, aborting tests")
            return self.test_results
        
        # Test 2: API Info
        self.test_api_info()
        
        # Test 3: Error Handling
        self.test_error_handling()
        
        # Test 4: Document Upload
        document_id = self.test_document_upload(test_file)
        if not document_id:
            logger.error("❌ Document upload failed, aborting remaining tests")
            return self.test_results
        
        # Test 5: Document Status
        self.test_document_status(document_id)
        
        # Test 6: Wait for Completion
        if not self.wait_for_completion(document_id):
            logger.error("❌ Document processing failed, aborting remaining tests")
            return self.test_results
        
        # Test 7: Processing Results
        self.test_processing_results(document_id)
        
        # Test 8: Output Files
        self.test_output_files(document_id)
        
        # Test 9: Performance Metrics
        self.test_performance_metrics(document_id)
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 50)
        logger.info("📊 INTEGRATION TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"✅ Passed: {self.test_results['passed']}")
        logger.info(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            logger.info("\n🔍 FAILED TESTS:")
            for error in self.test_results['errors']:
                logger.error(f"  - {error}")
        
        success_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100
        logger.info(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("🎉 Integration test PASSED!")
        elif success_rate >= 70:
            logger.info("⚠️  Integration test PARTIALLY PASSED")
        else:
            logger.info("💥 Integration test FAILED!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR API Integration Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--file", default="samples/1.pdf", help="Test PDF file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if test file exists
    if not os.path.exists(args.file):
        logger.error(f"❌ Test file not found: {args.file}")
        sys.exit(1)
    
    # Run integration tests
    tester = OCRAPITester(args.url)
    results = tester.run_full_integration_test(args.file)
    tester.print_summary()
    
    # Exit with appropriate code
    success_rate = (results['passed'] / results['total_tests']) * 100
    sys.exit(0 if success_rate >= 90 else 1)

if __name__ == "__main__":
    main()
