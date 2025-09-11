#!/usr/bin/env python3
"""
Final comprehensive test script for OCR API and Case Management system
This script properly handles asynchronous processing and waits for completion

Updated to reflect recent improvements:
- Uses proper two-step workflow: case creation followed by document addition
- Includes idempotency keys for reliable document addition
- Supports file:// URLs for document references
- Enhanced error handling and detailed reporting
"""

import pytest
import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any

# Configuration
OCR_API_BASE = "http://localhost:8000"
CASE_API_BASE = "http://localhost:8001"
SAMPLES_DIR = "data/samples"
TEST_TIMEOUT = 300  # 5 minutes max wait time
POLL_INTERVAL = 2   # Check status every 2 seconds

def check_api_health(api_base: str, api_name: str) -> bool:
    """Test if API is healthy"""
    try:
        # Use different health endpoints for different APIs
        if "8001" in api_base:  # Case Management API
            health_url = f"{api_base}/v1/health"
        else:  # OCR API
            health_url = f"{api_base}/health"
            
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {api_name} is healthy")
            return True
        else:
            print(f"❌ {api_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {api_name} health check failed: {e}")
        return False

def upload_and_process_pdf(file_path: str, relative_path: str = None) -> Dict[str, Any]:
    """Upload PDF and wait for processing to complete with hierarchy enhancement"""
    filename = os.path.basename(file_path)
    print(f"\n📄 Processing {file_path}...")
    
    try:
        # Upload file with hierarchy enhancement
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            data = {'language': 'vie+eng'}  # Support both Vietnamese and English
            
            # Add hierarchy enhancement: preserve folder structure in output
            if relative_path:
                data['relative_input_path'] = relative_path
                print(f"📁 Using hierarchy enhancement with relative path: {relative_path}")
            
            response = requests.post(
                f"{OCR_API_BASE}/documents/transform",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"Upload failed: {response.status_code} - {response.text}",
                'filename': filename
            }
        
        upload_result = response.json()
        document_id = upload_result['document_id']
        print(f"📤 Uploaded {filename}, document ID: {document_id}")
        
        # Wait for processing to complete
        start_time = time.time()
        while time.time() - start_time < TEST_TIMEOUT:
            try:
                status_response = requests.get(
                    f"{OCR_API_BASE}/documents/status/{document_id}",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    progress = status_data['progress']
                    
                    print(f"⏳ Status: {status}, Progress: {progress:.1%}")
                    
                    if status == 'completed':
                        result = status_data.get('result', {})
                        total_pages = result.get('total_pages', 0)
                        processing_time = result.get('processing_time', 0)
                        issues_detected = result.get('issues_detected', False)
                        
                        print(f"✅ {filename} processed successfully!")
                        print(f"   📊 Pages: {total_pages}, Time: {processing_time:.2f}s, Issues: {issues_detected}")
                        
                        return {
                            'success': True,
                            'filename': filename,
                            'document_id': document_id,
                            'total_pages': total_pages,
                            'processing_time': processing_time,
                            'issues_detected': issues_detected,
                            'result': result
                        }
                    
                    elif status == 'failed':
                        error = status_data.get('error', 'Unknown error')
                        print(f"❌ {filename} processing failed: {error}")
                        return {
                            'success': False,
                            'error': f"Processing failed: {error}",
                            'filename': filename
                        }
                    
                    # Still processing, wait and check again
                    time.sleep(POLL_INTERVAL)
                    
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return {
                        'success': False,
                        'error': f"Status check failed: {status_response.status_code}",
                        'filename': filename
                    }
                    
            except Exception as e:
                print(f"❌ Error checking status: {e}")
                time.sleep(POLL_INTERVAL)
        
        # Timeout
        print(f"⏰ {filename} processing timed out after {TEST_TIMEOUT}s")
        return {
            'success': False,
            'error': f"Processing timed out after {TEST_TIMEOUT}s",
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return {
            'success': False,
            'error': str(e),
            'filename': filename
        }

@pytest.fixture
def sample_pdf_path():
    """Fixture to provide a sample PDF path for testing"""
    samples_dir = Path(SAMPLES_DIR)
    if not samples_dir.exists():
        pytest.skip(f"Samples directory {SAMPLES_DIR} not found")
    
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("No PDF files found in samples directory")
    
    return str(pdf_files[0])

@pytest.fixture
def ocr_result(sample_pdf_path):
    """Fixture to process a PDF and return OCR result"""
    return upload_and_process_pdf(sample_pdf_path)

def test_api_health():
    """Test if both APIs are healthy"""
    ocr_healthy = check_api_health(OCR_API_BASE, "OCR API")
    case_healthy = check_api_health(CASE_API_BASE, "Case Management API")
    
    assert ocr_healthy, "OCR API health check failed"
    assert case_healthy, "Case Management API health check failed"

def test_case_management_integration(ocr_result: Dict[str, Any]):
    """Test case management integration with OCR result using proper document addition workflow"""
    assert ocr_result.get('success'), f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}"
    
    try:
        # Step 1: Create a case
        case_data = {
            "name": f"Legal Document Analysis - {ocr_result['filename']}",
            "description": f"Automated case created for document {ocr_result['filename']} with {ocr_result.get('total_pages', 0)} pages",
            "priority": 5  # Changed to integer as expected by API
        }
        
        # Include required idempotency key header
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": f"test-case-{ocr_result['document_id']}"
        }
        
        response = requests.post(
            f"{CASE_API_BASE}/v1/cases",  # Fixed endpoint path
            json=case_data,
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Case creation failed: {response.status_code} - {response.text}"
        
        case_result = response.json()
        case_id = case_result.get('case_id')  # Fixed field name
        print(f"✅ Case created successfully: {case_id}")
        
        # Step 2: Add document to case using the fixed document addition endpoint
        # Get output directory from OCR result if available
        output_dir = ocr_result.get('result', {}).get('output_directory', '')
        document_url = f"file://{os.path.abspath(output_dir)}" if output_dir else None
        
        document_data = {
            "filename": ocr_result['filename'],
            "url": document_url,
            "metadata": {
                "ocr_document_id": ocr_result['document_id'],
                "pages": ocr_result.get('total_pages', 0),
                "processing_time": ocr_result.get('processing_time', 0),
                "issues_detected": ocr_result.get('issues_detected', False),
                "ocr_result": ocr_result.get('result', {})
            }
        }
        
        # Include idempotency key for reliable document addition
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": f"test-doc-{case_id}-{ocr_result['document_id']}"
        }
        
        doc_response = requests.post(
            f"{CASE_API_BASE}/v1/cases/{case_id}/documents",
            json=document_data,
            headers=headers,
            timeout=30
        )
        
        assert doc_response.status_code == 200, f"Document addition failed: {doc_response.status_code} - {doc_response.text}"
        
        doc_result = doc_response.json()
        print(f"✅ Document added to case successfully: {doc_result.get('document_id')}")
        
        # Verify the integration was successful
        assert case_id is not None, "Case ID should not be None"
        assert doc_result.get('document_id') is not None, "Document ID should not be None"
            
    except Exception as e:
        print(f"❌ Case management error: {e}")
        pytest.fail(f"Case management integration failed: {str(e)}")

def main():
    """Main test function for manual testing"""
    print("🚀 Starting comprehensive OCR and Case Management tests...\n")
    
    # Test API health
    print("=== API Health Checks ===")
    ocr_healthy = check_api_health(OCR_API_BASE, "OCR API")
    case_healthy = check_api_health(CASE_API_BASE, "Case Management API")
    
    if not ocr_healthy:
        print("\n❌ OCR API is not available. Please start the OCR API first.")
        return
    
    # Find PDF files recursively in samples folder including subfolders
    pdf_files = []
    samples_path = Path(SAMPLES_DIR)
    
    if samples_path.exists():
        # Recursively find all PDF files
        for pdf_file in samples_path.rglob('*.pdf'):
            pdf_files.append(str(pdf_file))
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in {SAMPLES_DIR} directory (including subfolders)")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDF files to test (including subfolders):")
    for pdf_file in pdf_files:
        print(f"   📄 {pdf_file}")
    
    # Process each PDF with hierarchy enhancement
    print("\n=== OCR Processing Tests with Hierarchy Enhancement ===")
    results = []
    successful_ocr = []
    
    for pdf_file in pdf_files:
        # Calculate relative path for hierarchy enhancement
        pdf_path = Path(pdf_file)
        samples_path = Path(SAMPLES_DIR)
        
        try:
            # Get relative path from samples directory
            relative_to_samples = pdf_path.relative_to(samples_path)
            # Get the parent directory path (excluding the filename)
            relative_dir = str(relative_to_samples.parent) if relative_to_samples.parent != Path('.') else None
        except ValueError:
            # If file is not under samples directory, use None
            relative_dir = None
        
        result = upload_and_process_pdf(pdf_file, relative_dir)
        results.append(result)
        if result['success']:
            successful_ocr.append(result)
    
    # Test case management integration
    if case_healthy and successful_ocr:
        print("\n=== Case Management Integration Tests ===")
        for ocr_result in successful_ocr[:2]:  # Test with first 2 successful OCR results
            case_result = test_case_management_integration(ocr_result)
            ocr_result['case_management'] = case_result
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    successful_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
    
    print(f"OCR Processing: {successful_count}/{total_count} successful ({success_rate:.1f}%)")
    
    if case_healthy:
        case_success_count = sum(1 for r in successful_ocr if r and r.get('case_management') and r.get('case_management', {}).get('success', False))
        case_total = len(successful_ocr)
        case_success_rate = (case_success_count / case_total * 100) if case_total > 0 else 0
        print(f"Case Management Integration: {case_success_count}/{case_total} successful ({case_success_rate:.1f}%)")
        
        # Additional details for case management
        case_created_count = sum(1 for r in successful_ocr if r and r.get('case_management') and r.get('case_management', {}).get('case_id'))
        doc_added_count = sum(1 for r in successful_ocr if r and r.get('case_management') and r.get('case_management', {}).get('document_id'))
        print(f"  - Cases created: {case_created_count}/{case_total}")
        print(f"  - Documents added: {doc_added_count}/{case_total}")
    
    # Detailed results
    print("\n📋 Detailed Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        filename = result['filename']
        if result['success']:
            pages = result.get('total_pages', 0)
            time_taken = result.get('processing_time', 0)
            print(f"  {status} {filename}: {pages} pages, {time_taken:.2f}s")
        else:
            error = result.get('error', 'Unknown error')
            print(f"  {status} {filename}: {error}")
    
    # Save detailed results
    output_file = "final_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'ocr_success_rate': success_rate,
                'total_files': total_count,
                'successful_files': successful_count
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to {output_file}")
    
    if success_rate == 100:
        print("\n🎉 All tests passed successfully!")
    elif success_rate >= 75:
        print("\n✅ Most tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the results above.")

if __name__ == "__main__":
    main()