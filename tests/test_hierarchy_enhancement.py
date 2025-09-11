#!/usr/bin/env python3
"""
Test script for API Output Hierarchy Enhancement
Tests the new relative_input_path parameter functionality
"""

import requests
import json
import time
from pathlib import Path

# Import test configuration
from test_config import TestEnvironment

# API configuration
API_BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "data/samples/1.pdf"  # Using existing sample file

def test_hierarchy_enhancement():
    """Test the new relative_input_path parameter"""
    
    print("🧪 Testing API Output Hierarchy Enhancement")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Default behavior (no relative_input_path)",
            "relative_input_path": None,
            "expected_output": "output/1/"
        },
        {
            "name": "Folder1 hierarchy", 
            "relative_input_path": "folder1",
            "expected_output": "output/folder1/1/"
        },
        {
            "name": "Folder2 hierarchy",
            "relative_input_path": "folder2", 
            "expected_output": "output/folder2/1/"
        },
        {
            "name": "Nested folder hierarchy",
            "relative_input_path": "samples/subfolder",
            "expected_output": "output/samples/subfolder/1/"
        }
    ]
    
    # Check if test PDF exists
    if not Path(TEST_PDF_PATH).exists():
        print(f"⚠️  Test PDF not found at {TEST_PDF_PATH}")
        print("Please ensure you have a test PDF file available")
        return
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Expected output: {test_case['expected_output']}")
        
        # Prepare request data
        files = {'file': open(TEST_PDF_PATH, 'rb')}
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
                while True:
                    status_response = requests.get(f"{API_BASE_URL}/documents/status/{document_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data['status'] == 'completed':
                            print("✅ Processing completed!")
                            if 'result' in status_data and status_data['result']:
                                output_dir = status_data['result'].get('output_directory')
                                if output_dir:
                                    print(f"📁 Output directory: {output_dir}")
                                    # Verify the directory structure
                                    if Path(output_dir).exists():
                                        print(f"✅ Output directory exists: {output_dir}")
                                    else:
                                        print(f"❌ Output directory not found: {output_dir}")
                            break
                        elif status_data['status'] == 'failed':
                            print(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                            break
                        else:
                            print(f"⏳ Status: {status_data['status']} ({status_data['progress']:.1%})")
                            time.sleep(2)
                    else:
                        print(f"❌ Failed to get status: {status_response.status_code}")
                        break
            else:
                print(f"❌ Failed to submit document: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
        
        print("-" * 30)
    
    print("\n🎯 Test Summary")
    print("Check the output/ directory to verify the hierarchical structure:")
    print("- output/1/ (default behavior)")
    print("- output/folder1/1/ (folder1 hierarchy)")
    print("- output/folder2/1/ (folder2 hierarchy)")
    print("- output/samples/subfolder/1/ (nested hierarchy)")

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"Make sure the API is running on {API_BASE_URL}")
        return False

if __name__ == "__main__":
    print("🚀 API Output Hierarchy Enhancement Test")
    print("=" * 50)
    
    # Use dedicated test output directory
    with TestEnvironment():
        print("📁 Using dedicated test output directory")
        
        # Check API health first
        if check_api_health():
            test_hierarchy_enhancement()
        else:
            print("\n💡 To start the API, run: python api.py")