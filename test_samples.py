#!/usr/bin/env python3
"""
Comprehensive test script for OCR API and Case Management system.
Tests all PDF files in the samples folder through both APIs.
"""

import os
import json
import time
import requests
from pathlib import Path
import uuid
from typing import List, Dict, Any

# API Configuration
OCR_API_BASE = "http://localhost:8000"
CASE_API_BASE = "http://localhost:8001/v1"
SAMPLES_DIR = "samples"
OUTPUT_DIR = "output"

class TestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            self.tests_failed += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "details": details
        }
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ({self.tests_passed/self.tests_run*100:.1f}%)")
        print(f"Failed: {self.tests_failed} ({self.tests_failed/self.tests_run*100:.1f}%)")
        print("="*60)
        
        if self.tests_failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if "❌" in result["status"]:
                    print(f"- {result['test']}: {result['details']}")

def check_api_health(base_url: str, api_name: str) -> bool:
    """Check if API is healthy and responding."""
    try:
        if "8001" in base_url:
            response = requests.get(f"{base_url}/health", timeout=5)
        else:
            response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {api_name} health check failed: {e}")
        return False

def get_pdf_files() -> List[Path]:
    """Get all PDF files from samples directory."""
    samples_path = Path(SAMPLES_DIR)
    if not samples_path.exists():
        print(f"❌ Samples directory {SAMPLES_DIR} does not exist")
        return []
    
    pdf_files = list(samples_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {SAMPLES_DIR}/")
    for pdf_file in pdf_files:
        size = pdf_file.stat().st_size
        print(f"  - {pdf_file.name} ({size:,} bytes)")
    
    return pdf_files

def test_ocr_api_direct(pdf_file: Path, results: TestResults):
    """Test OCR API directly with a PDF file."""
    test_name = f"OCR Direct: {pdf_file.name}"
    
    try:
        # Upload file for processing
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            data = {
                'language': 'vie' if '1.pdf' in str(pdf_file) else 'eng',
                'enable_handwriting_detection': 'false'
            }
            
            response = requests.post(
                f"{OCR_API_BASE}/documents/transform",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            results.add_result(test_name, False, f"Upload failed: {response.status_code}")
            return None
        
        upload_result = response.json()
        document_id = upload_result.get('document_id')
        
        if not document_id:
            results.add_result(test_name, False, "No document_id returned")
            return None
        
        # Poll for completion
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"{OCR_API_BASE}/documents/{document_id}/status",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                
                if status == 'completed':
                    processing_time = status_data.get('processing_time', 0)
                    total_pages = status_data.get('total_pages', 0)
                    results.add_result(
                        test_name, 
                        True, 
                        f"Processed {total_pages} pages in {processing_time:.2f}s"
                    )
                    return document_id
                elif status == 'failed':
                    results.add_result(test_name, False, "Processing failed")
                    return None
                elif status == 'processing':
                    time.sleep(2)
                    continue
            
            time.sleep(1)
        
        results.add_result(test_name, False, "Timeout waiting for completion")
        return None
        
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")
        return None

def test_case_management_workflow(pdf_files: List[Path], results: TestResults):
    """Test complete case management workflow with all PDF files."""
    
    # Test 1: Create a case
    test_name = "Case Management: Create Case"
    try:
        case_data = {
            "name": "Sample PDF Test Case",
            "description": "Testing all sample PDF files through case management workflow",
            "metadata": {
                "test_run": True,
                "pdf_count": len(pdf_files),
                "timestamp": time.time()
            },
            "priority": 8
        }
        
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        }
        
        response = requests.post(
            f"{CASE_API_BASE}/cases",
            json=case_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 201:
            results.add_result(test_name, False, f"Failed to create case: {response.status_code}")
            return
        
        case_result = response.json()
        case_id = case_result.get('case_id')
        
        if not case_id:
            results.add_result(test_name, False, "No case_id returned")
            return
        
        results.add_result(test_name, True, f"Created case: {case_id}")
        
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")
        return
    
    # Test 2: Add documents to case
    document_ids = []
    for pdf_file in pdf_files:
        test_name = f"Case Management: Add Document {pdf_file.name}"
        try:
            # Convert file path to file:// URL
            file_url = f"file://{pdf_file.absolute()}"
            
            doc_data = {
                "filename": pdf_file.name,
                "url": file_url,
                "metadata": {
                    "file_size": pdf_file.stat().st_size,
                    "language": "vietnamese" if "1.pdf" in pdf_file.name else "english"
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Idempotency-Key": str(uuid.uuid4())
            }
            
            response = requests.post(
                f"{CASE_API_BASE}/cases/{case_id}/documents",
                json=doc_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                doc_result = response.json()
                document_id = doc_result.get('document_id')
                document_ids.append(document_id)
                results.add_result(test_name, True, f"Added document: {document_id}")
            else:
                results.add_result(test_name, False, f"Failed: {response.status_code}")
                
        except Exception as e:
            results.add_result(test_name, False, f"Exception: {str(e)}")
    
    # Test 3: Create OCR job
    test_name = "Case Management: Create OCR Job"
    try:
        job_data = {
            "case_ids": [case_id],
            "language": "vie",
            "enable_handwriting_detection": False,
            "priority": 7,
            "metadata": {
                "test_job": True,
                "document_count": len(document_ids)
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        }
        
        response = requests.post(
            f"{CASE_API_BASE}/jobs",
            json=job_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            job_result = response.json()
            job_id = job_result.get('job_id')
            results.add_result(test_name, True, f"Created job: {job_id}")
        else:
            results.add_result(test_name, False, f"Failed: {response.status_code}")
            
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")
    
    # Test 4: Check case status
    test_name = "Case Management: Check Case Status"
    try:
        response = requests.get(
            f"{CASE_API_BASE}/cases/{case_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            case_data = response.json()
            status = case_data.get('status')
            doc_count = len(case_data.get('documents', []))
            results.add_result(
                test_name, 
                True, 
                f"Status: {status}, Documents: {doc_count}"
            )
        else:
            results.add_result(test_name, False, f"Failed: {response.status_code}")
            
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")
    
    # Test 5: List cases with pagination
    test_name = "Case Management: List Cases"
    try:
        response = requests.get(
            f"{CASE_API_BASE}/cases?limit=10",
            timeout=10
        )
        
        if response.status_code == 200:
            cases_data = response.json()
            case_count = len(cases_data.get('cases', []))
            results.add_result(test_name, True, f"Found {case_count} cases")
        else:
            results.add_result(test_name, False, f"Failed: {response.status_code}")
            
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")

def test_system_metrics(results: TestResults):
    """Test system monitoring endpoints."""
    
    # Test metrics endpoint
    test_name = "System: Metrics"
    try:
        response = requests.get(f"{CASE_API_BASE}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics = response.json()
            case_count = metrics.get('total_cases', 0)
            job_count = metrics.get('total_jobs', 0)
            results.add_result(
                test_name, 
                True, 
                f"Cases: {case_count}, Jobs: {job_count}"
            )
        else:
            results.add_result(test_name, False, f"Failed: {response.status_code}")
            
    except Exception as e:
        results.add_result(test_name, False, f"Exception: {str(e)}")

def check_output_files(document_ids: List[str], results: TestResults):
    """Check if output files were created correctly."""
    output_path = Path(OUTPUT_DIR)
    
    for doc_id in document_ids:
        if not doc_id:
            continue
            
        test_name = f"Output Files: {doc_id}"
        doc_output_dir = output_path / doc_id
        
        if not doc_output_dir.exists():
            results.add_result(test_name, False, "Output directory not found")
            continue
        
        # Check for analysis file
        analysis_file = doc_output_dir / f"{doc_id}_analysis.json"
        pdf_dir = doc_output_dir / "pdf"
        text_dir = doc_output_dir / "text"
        
        files_found = []
        if analysis_file.exists():
            files_found.append("analysis.json")
        if pdf_dir.exists():
            pdf_count = len(list(pdf_dir.glob("*.pdf")))
            files_found.append(f"{pdf_count} PDF files")
        if text_dir.exists():
            txt_count = len(list(text_dir.glob("*.txt")))
            files_found.append(f"{txt_count} text files")
        
        if files_found:
            results.add_result(test_name, True, ", ".join(files_found))
        else:
            results.add_result(test_name, False, "No output files found")

def main():
    print("🚀 Starting Comprehensive OCR and Case Management Tests")
    print("="*60)
    
    results = TestResults()
    
    # Check API health
    print("\n📋 Checking API Health...")
    ocr_healthy = check_api_health(OCR_API_BASE, "OCR API")
    case_healthy = check_api_health(CASE_API_BASE, "Case Management API")
    
    results.add_result("OCR API Health", ocr_healthy)
    results.add_result("Case Management API Health", case_healthy)
    
    if not ocr_healthy or not case_healthy:
        print("\n❌ One or more APIs are not healthy. Please start the servers:")
        print("   Terminal 1: python api.py")
        print("   Terminal 2: python case_management_api.py")
        results.print_summary()
        return
    
    # Get PDF files
    print("\n📁 Scanning for PDF files...")
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        print("❌ No PDF files found in samples/ directory")
        results.print_summary()
        return
    
    # Test OCR API directly
    print("\n🔍 Testing OCR API directly...")
    document_ids = []
    for pdf_file in pdf_files:
        doc_id = test_ocr_api_direct(pdf_file, results)
        if doc_id:
            document_ids.append(doc_id)
    
    # Test Case Management workflow
    print("\n📋 Testing Case Management workflow...")
    test_case_management_workflow(pdf_files, results)
    
    # Test system metrics
    print("\n📊 Testing system monitoring...")
    test_system_metrics(results)
    
    # Check output files
    print("\n📄 Checking output files...")
    check_output_files(document_ids, results)
    
    # Print final summary
    results.print_summary()
    
    # Save detailed results
    results_file = "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "summary": {
                "total_tests": results.tests_run,
                "passed": results.tests_passed,
                "failed": results.tests_failed,
                "success_rate": f"{results.tests_passed/results.tests_run*100:.1f}%"
            },
            "results": results.results
        }, f, indent=2)
    
    print(f"\n📋 Detailed results saved to {results_file}")
    
    if results.tests_failed == 0:
        print("\n🎉 All tests passed! The OCR and Case Management system is working correctly.")
    else:
        print(f"\n⚠️  {results.tests_failed} test(s) failed. Check the details above.")

if __name__ == "__main__":
    main()