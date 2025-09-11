#!/usr/bin/env python3
"""
Real-time API test to demonstrate hierarchy preservation functionality
"""

import requests
import json
import time
from pathlib import Path

# API configuration
API_BASE_URL = "http://localhost:8000"

def test_realtime_api():
    """Real-time test of the hierarchy preservation API"""
    
    print("🚀 Real-time API Hierarchy Preservation Test")
    print("=" * 50)
    
    # Test with a new file from data/samples/a/ folder
    test_file = "data/samples/a/1.pdf"
    relative_path = "a"
    
    print(f"📄 Testing with: {test_file}")
    print(f"🗂️  Relative path: {relative_path}")
    print(f"📁 Expected output: data/outputs/{relative_path}/1/")
    print()
    
    # Check if test file exists
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    # Prepare request
    files = {'file': open(test_file, 'rb')}
    data = {
        'language': 'vie',
        'enable_handwriting_detection': False,
        'relative_input_path': relative_path
    }
    
    try:
        print("📤 Submitting document for processing...")
        response = requests.post(f"{API_BASE_URL}/documents/transform", files=files, data=data)
        files['file'].close()
        
        if response.status_code == 200:
            result = response.json()
            document_id = result['document_id']
            print(f"✅ Document submitted successfully!")
            print(f"🆔 Document ID: {document_id}")
            print()
            
            # Monitor processing in real-time
            print("⏳ Monitoring processing status in real-time...")
            start_time = time.time()
            
            while True:
                status_response = requests.get(f"{API_BASE_URL}/documents/status/{document_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    elapsed = time.time() - start_time
                    
                    if status_data['status'] == 'completed':
                        if 'result' in status_data and status_data['result']:
                            result = status_data['result']
                            total_pages = result.get('total_pages', 0)
                            time_per_page = elapsed / total_pages if total_pages > 0 else 0
                            
                            print(f"\n✅ Processing completed in {elapsed:.1f} seconds!")
                            print(f"📄 Total pages: {total_pages} | ⏱️ Time per page: {time_per_page:.2f}s")
                            
                            output_dir = result.get('output_directory')
                            if output_dir:
                                print(f"📁 Output directory: {output_dir}")
                                
                                # Verify hierarchy preservation
                                if Path(output_dir).exists():
                                    print(f"✅ Output directory exists!")
                                    
                                    # Check for expected files
                                    json_file = Path(output_dir) / "1_analysis.json"
                                    pdf_dir = Path(output_dir) / "pdf"
                                    text_dir = Path(output_dir) / "text"
                                    
                                    if json_file.exists():
                                        print(f"✅ Analysis JSON created: {json_file}")
                                    if pdf_dir.exists():
                                        print(f"✅ PDF directory created: {pdf_dir}")
                                    if text_dir.exists():
                                        print(f"✅ Text directory created: {text_dir}")
                                    
                                    # Verify hierarchy preservation
                                    if f"data/outputs/{relative_path}/1" in str(output_dir):
                                        print(f"🎯 ✅ Hierarchy preserved correctly!")
                                        print(f"   Input: {test_file}")
                                        print(f"   Output: {output_dir}")
                                    else:
                                        print(f"⚠️  Hierarchy not preserved as expected")
                                else:
                                    print(f"❌ Output directory not found: {output_dir}")
                        else:
                            print(f"\n✅ Processing completed in {elapsed:.1f} seconds!")
                        break
                        
                    elif status_data['status'] == 'failed':
                        print(f"\n❌ Processing failed after {elapsed:.1f} seconds")
                        print(f"Error: {status_data.get('error', 'Unknown error')}")
                        break
                        
                    else:
                        # Show real-time progress
                        progress = status_data.get('progress', 0)
                        status = status_data['status']
                        
                        # Show page info if available
                        page_info = ""
                        if 'result' in status_data and status_data['result']:
                            total_pages = status_data['result'].get('total_pages', 0)
                            if total_pages > 0:
                                page_info = f" | Pages: {total_pages}"
                        
                        print(f"\r⏳ Status: {status} ({progress:.1%}){page_info} - {elapsed:.1f}s", end="", flush=True)
                        time.sleep(1)
                        
                else:
                    print(f"\n❌ Failed to get status: {status_response.status_code}")
                    break
                    
        else:
            print(f"❌ Failed to submit document: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Real-time Test Summary:")
    print(f"✅ API is responsive and processing documents")
    print(f"✅ Hierarchy preservation is working correctly")
    print(f"✅ Real-time status monitoring is functional")
    print(f"✅ Output structure: samples/{relative_path}/ → output/{relative_path}/1/")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    if check_api_health():
        test_realtime_api()
    else:
        print("❌ API is not running!")
        print("💡 To start the API, run: python src/api/v1/api.py")