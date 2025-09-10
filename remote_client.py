#!/usr/bin/env python3
"""
Remote OCR API Client

This script allows you to access the OCR API from your local computer.
It supports both direct access and SSH tunnel methods.
"""

import requests
import time
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

class RemoteOCRClient:
    def __init__(self, base_url: str = "http://10.148.0.2:8000"):
        """
        Initialize the remote OCR client
        
        Args:
            base_url: API base URL (use localhost:8000 for SSH tunnel)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def health_check(self) -> Optional[Dict[str, Any]]:
        """Check API health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Get API information"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API info failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def process_document(self, file_path: str, language: str = "vie", 
                        enable_handwriting: bool = False, 
                        max_wait: int = 300) -> Optional[Dict[str, Any]]:
        """
        Process a document and return results
        
        Args:
            file_path: Path to PDF file
            language: Language code (default: 'vie' for Vietnamese)
            enable_handwriting: Enable handwriting detection
            max_wait: Maximum wait time in seconds
        
        Returns:
            Processing results or None if failed
        """
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return None
        
        print(f"📤 Uploading document: {file_path}")
        
        try:
            # Upload document
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'language': language,
                    'enable_handwriting_detection': str(enable_handwriting).lower()
                }
                
                response = self.session.post(
                    f"{self.base_url}/documents/transform",
                    files=files,
                    data=data
                )
            
            if response.status_code != 200:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            document_id = result['document_id']
            print(f"✅ Document uploaded successfully: {document_id}")
            
            # Wait for completion
            return self.wait_for_completion(document_id, max_wait)
            
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def wait_for_completion(self, document_id: str, max_wait: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for document processing to complete"""
        print(f"⏳ Waiting for processing to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(f"{self.base_url}/documents/status/{document_id}")
                if response.status_code != 200:
                    print(f"❌ Status check failed: {response.status_code}")
                    return None
                
                data = response.json()
                status = data['status']
                progress = data['progress']
                
                print(f"📊 Status: {status}, Progress: {progress:.1%}")
                
                if status == 'completed':
                    print("✅ Processing completed!")
                    return data['result']
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print(f"❌ Processing failed: {error}")
                    return None
                
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Status check error: {e}")
                return None
        
        print(f"⏰ Processing timeout after {max_wait} seconds")
        return None
    
    def get_document_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status"""
        try:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Remote OCR API Client")
    parser.add_argument("--url", default="http://10.148.0.2:8000", 
                       help="API base URL (use localhost:8000 for SSH tunnel)")
    parser.add_argument("--file", "-f", help="PDF file to process")
    parser.add_argument("--language", "-l", default="vie", 
                       help="Language code (default: vie)")
    parser.add_argument("--handwriting", action="store_true", 
                       help="Enable handwriting detection")
    parser.add_argument("--status", "-s", help="Check status of document ID")
    parser.add_argument("--health", action="store_true", 
                       help="Check API health")
    parser.add_argument("--info", action="store_true", 
                       help="Get API information")
    parser.add_argument("--wait", "-w", type=int, default=300, 
                       help="Maximum wait time in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Initialize client
    client = RemoteOCRClient(args.url)
    
    print("🔍 Remote OCR API Client")
    print("=" * 40)
    print(f"API URL: {args.url}")
    print()
    
    # Health check
    if args.health or not any([args.file, args.status, args.info]):
        print("🏥 Checking API health...")
        health = client.health_check()
        if health:
            print(f"✅ API Status: {health['status']}")
            print(f"📊 Active Tasks: {health['active_tasks']}")
            print(f"🕐 Timestamp: {health['timestamp']}")
        else:
            print("❌ API is not accessible")
            return 1
    
    # API info
    if args.info:
        print("\n📋 Getting API information...")
        info = client.get_api_info()
        if info:
            print(f"📝 Message: {info['message']}")
            print(f"🔢 Version: {info['version']}")
            print("🔗 Available Endpoints:")
            for endpoint, path in info['endpoints'].items():
                print(f"  - {endpoint}: {path}")
        else:
            print("❌ Failed to get API information")
    
    # Check document status
    if args.status:
        print(f"\n📊 Checking status for document: {args.status}")
        status = client.get_document_status(args.status)
        if status:
            print(f"Status: {status['status']}")
            print(f"Progress: {status['progress']:.1%}")
            if 'result' in status:
                result = status['result']
                print(f"Pages: {result['total_pages']}")
                print(f"Processing Time: {result['processing_time']:.2f}s")
        else:
            print("❌ Failed to get document status")
    
    # Process document
    if args.file:
        print(f"\n📄 Processing document: {args.file}")
        result = client.process_document(
            args.file, 
            language=args.language,
            enable_handwriting=args.handwriting,
            max_wait=args.wait
        )
        
        if result:
            print("\n🎉 Processing Results:")
            print(f"📄 Document ID: {result['document_id']}")
            print(f"📊 Total Pages: {result['total_pages']}")
            print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
            print(f"📁 Output Directory: {result['output_directory']}")
            print(f"🔍 Issues Detected: {result['issues_detected']}")
            
            if 'pages' in result:
                print(f"\n📋 Page Details:")
                for page in result['pages']:
                    print(f"  Page {page['page_number']}: {len(page['extracted_text'])} chars")
        else:
            print("❌ Document processing failed")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
