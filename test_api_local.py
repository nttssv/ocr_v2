#!/usr/bin/env python3
"""
Simple API Test Script

This script demonstrates that the API is working locally.
"""

import requests
import json

def test_api():
    """Test the API locally"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing OCR API locally...")
    print("=" * 40)
    
    try:
        # Test health
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health: {data['status']}")
            print(f"   📊 Active Tasks: {data['active_tasks']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test info
        print("\n2. Testing info endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Version: {data['version']}")
            print(f"   📝 Message: {data['message']}")
        else:
            print(f"   ❌ Info check failed: {response.status_code}")
            return False
        
        # Test document upload
        print("\n3. Testing document upload...")
        try:
            with open("samples/1.pdf", "rb") as f:
                files = {"file": f}
                data = {
                    "language": "vie",
                    "enable_handwriting_detection": "false"
                }
                
                response = requests.post(
                    f"{base_url}/documents/transform",
                    files=files,
                    data=data,
                    timeout=10
                )
            
            if response.status_code == 200:
                result = response.json()
                document_id = result["document_id"]
                print(f"   ✅ Document uploaded: {document_id}")
                
                # Check status
                print("\n4. Checking processing status...")
                status_response = requests.get(f"{base_url}/documents/status/{document_id}", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   📊 Status: {status_data['status']}")
                    print(f"   📈 Progress: {status_data['progress']:.1%}")
                else:
                    print(f"   ❌ Status check failed: {status_response.status_code}")
            else:
                print(f"   ❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except FileNotFoundError:
            print("   ⚠️  Sample file not found, skipping upload test")
        
        print("\n🎉 API is working correctly!")
        print("\n📋 To access from your local computer:")
        print("1. Create SSH tunnel: ssh -L 8000:localhost:8000 gcpcoder@35.240.229.181")
        print("2. Then use: curl http://localhost:8000/health")
        print("3. Or use Python client: python remote_client.py --url http://localhost:8000 --health")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_api()
