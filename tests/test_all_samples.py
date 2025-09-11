#!/usr/bin/env python3
"""
Comprehensive test to process ALL files in the samples directory
Including root-level files like samples/1.pdf and samples/2.pdf
"""

import requests
import json
import time
from pathlib import Path
import os

# API configuration
API_BASE_URL = "http://localhost:8000"

def test_all_samples():
    """Test processing of ALL PDF files in the samples directory"""
    
    print("🧪 Testing ALL Files in Samples Directory")
    print("=" * 50)
    
    # Find all PDF files in data/samples directory
    samples_dir = Path("data/samples")
    pdf_files = list(samples_dir.rglob("*.pdf"))
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    print()
    
    # Test cases for each file
    test_cases = []
    
    for pdf_file in pdf_files:
        # Calculate relative path from samples directory
        relative_to_samples = pdf_file.relative_to(samples_dir)
        
        # Determine the relative_input_path
        if relative_to_samples.parent == Path("."):
            # Root level file (data/samples/1.pdf, data/samples/2.pdf)
            relative_input_path = None  # No folder structure to preserve
            expected_output = f"data/outputs/{pdf_file.stem}/"
        else:
            # File in subfolder (data/samples/a/1.pdf, data/samples/legal/1.pdf, etc.)
            relative_input_path = str(relative_to_samples.parent)
            expected_output = f"data/outputs/{relative_to_samples.parent}/{pdf_file.stem}/"
        
        test_cases.append({
            "name": f"Process {pdf_file}",
            "file_path": str(pdf_file),
            "relative_input_path": relative_input_path,
            "expected_output": expected_output
        })
    
    # Process each file
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Input file: {test_case['file_path']}")
        print(f"Relative path: {test_case['relative_input_path']}")
        print(f"Expected output: {test_case['expected_output']}")
        
        # Check if test PDF exists
        if not Path(test_case['file_path']).exists():
            print(f"⚠️  Test PDF not found at {test_case['file_path']}")
            continue
        
        # Prepare request data
        files = {'file': open(test_case['file_path'], 'rb')}
        data = {
            'language': 'vie',
            'enable_handwriting_detection': False
        }
        
        # Add relative_input_path if specified
        if test_case['relative_input_path']:
            data['relative_input_path'] = test_case['relative_input_path']
        
        try:
            # Submit document for processing
            response = requests.post(f"{API_BASE_URL}/documents/transform", files=files, data=data)
            files['file'].close()
            
            if response.status_code == 200:
                result = response.json()
                document_id = result['document_id']
                print(f"✅ Document submitted successfully. ID: {document_id}")
                
                # Wait for processing to complete
                print("⏳ Waiting for processing...")
                start_time = time.time()
                
                while True:
                    status_response = requests.get(f"{API_BASE_URL}/documents/status/{document_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        elapsed_time = time.time() - start_time
                        
                        if status_data['status'] == 'completed':
                            if 'result' in status_data and status_data['result']:
                                result = status_data['result']
                                total_pages = result.get('total_pages', 0)
                                time_per_page = elapsed_time / total_pages if total_pages > 0 else 0
                                
                                print(f"✅ Processing completed in {elapsed_time:.1f} seconds!")
                                print(f"📄 Total pages: {total_pages} | ⏱️ Time per page: {time_per_page:.2f}s")
                                
                                output_dir = result.get('output_directory')
                                if output_dir:
                                    print(f"📁 Output directory: {output_dir}")
                                    # Verify the directory exists
                                    if Path(output_dir).exists():
                                        print(f"✅ Output directory exists: {output_dir}")
                                    else:
                                        print(f"❌ Output directory not found: {output_dir}")
                            else:
                                print(f"✅ Processing completed in {elapsed_time:.1f} seconds!")
                            break
                        elif status_data['status'] == 'failed':
                            print(f"❌ Processing failed after {elapsed_time:.1f} seconds: {status_data.get('error', 'Unknown error')}")
                            break
                        else:
                            progress = status_data.get('progress', 0)
                            # Calculate estimated time to completion
                            if progress > 0:
                                estimated_total = elapsed_time / progress
                                estimated_remaining = estimated_total - elapsed_time
                                
                                # Show page info if available
                                page_info = ""
                                if 'result' in status_data and status_data['result']:
                                    total_pages = status_data['result'].get('total_pages', 0)
                                    if total_pages > 0:
                                        page_info = f" | Pages: {total_pages}"
                                
                                print(f"⏳ Status: {status_data['status']} ({progress:.1%}){page_info} - Elapsed: {elapsed_time:.1f}s, ETA: {estimated_remaining:.1f}s")
                            else:
                                print(f"⏳ Status: {status_data['status']} ({progress:.1%}) - Elapsed: {elapsed_time:.1f}s")
                            time.sleep(2)
                    else:
                        print(f"❌ Failed to get status: {status_response.status_code}")
                        break
            else:
                print(f"❌ Failed to submit document: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
        
        print("-" * 40)
    
    print("\n🎯 Test Summary")
    print("All PDF files in the samples directory have been processed:")
    for test_case in test_cases:
        print(f"- {test_case['file_path']} → {test_case['expected_output']}")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Comprehensive Samples Directory Processing Test")
    print("This test processes ALL PDF files found in the samples directory.\n")
    
    if check_api_health():
        test_all_samples()
    else:
        print("❌ API is not running!")
        print("💡 To start the API, run: python src/api/v1/api.py")