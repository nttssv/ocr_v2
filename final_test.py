#!/usr/bin/env python3
"""
Final comprehensive test script for OCR API and Case Management system
This script properly handles asynchronous processing and waits for completion
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any

# Configuration
OCR_API_BASE = "http://localhost:8000"
CASE_API_BASE = "http://localhost:8001"
SAMPLES_DIR = "samples"
TEST_TIMEOUT = 300  # 5 minutes max wait time
POLL_INTERVAL = 2   # Check status every 2 seconds

def test_api_health(api_base: str, api_name: str) -> bool:
    """Test if API is healthy"""
    try:
        response = requests.get(f"{api_base}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {api_name} is healthy")
            return True
        else:
            print(f"❌ {api_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {api_name} health check failed: {e}")
        return False

def upload_and_process_pdf(file_path: str) -> Dict[str, Any]:
    """Upload PDF and wait for processing to complete"""
    filename = os.path.basename(file_path)
    print(f"\n📄 Processing {filename}...")
    
    try:
        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/pdf')}
            data = {'language': 'vie+eng'}  # Support both Vietnamese and English
            
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

def test_case_management_integration(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """Test case management integration with OCR result"""
    if not ocr_result.get('success'):
        return {'success': False, 'error': 'OCR processing failed'}
    
    try:
        # Create a case with OCR document
        case_data = {
            "title": f"Legal Document Analysis - {ocr_result['filename']}",
            "description": f"Automated case created for document {ocr_result['filename']} with {ocr_result.get('total_pages', 0)} pages",
            "priority": "medium",
            "documents": [{
                "document_id": ocr_result['document_id'],
                "filename": ocr_result['filename'],
                "pages": ocr_result.get('total_pages', 0),
                "processing_time": ocr_result.get('processing_time', 0),
                "issues_detected": ocr_result.get('issues_detected', False)
            }]
        }
        
        response = requests.post(
            f"{CASE_API_BASE}/cases",
            json=case_data,
            timeout=30
        )
        
        if response.status_code == 200:
            case_result = response.json()
            case_id = case_result.get('id')
            print(f"✅ Case created successfully: {case_id}")
            return {
                'success': True,
                'case_id': case_id,
                'case_data': case_result
            }
        else:
            print(f"❌ Case creation failed: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"Case creation failed: {response.status_code}"
            }
            
    except Exception as e:
        print(f"❌ Case management error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function"""
    print("🚀 Starting comprehensive OCR and Case Management tests...\n")
    
    # Test API health
    print("=== API Health Checks ===")
    ocr_healthy = test_api_health(OCR_API_BASE, "OCR API")
    case_healthy = test_api_health(CASE_API_BASE, "Case Management API")
    
    if not ocr_healthy:
        print("\n❌ OCR API is not available. Please start the OCR API first.")
        return
    
    # Find PDF files
    pdf_files = []
    if os.path.exists(SAMPLES_DIR):
        for file in os.listdir(SAMPLES_DIR):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(SAMPLES_DIR, file))
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in {SAMPLES_DIR} directory")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDF files to test")
    
    # Process each PDF
    print("\n=== OCR Processing Tests ===")
    results = []
    successful_ocr = []
    
    for pdf_file in pdf_files:
        result = upload_and_process_pdf(pdf_file)
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
        case_success_count = sum(1 for r in successful_ocr if r.get('case_management', {}).get('success', False))
        case_total = len(successful_ocr)
        case_success_rate = (case_success_count / case_total * 100) if case_total > 0 else 0
        print(f"Case Management: {case_success_count}/{case_total} successful ({case_success_rate:.1f}%)")
    
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