#!/usr/bin/env python3
"""
OCR API Hierarchy Enhancement - Usage Examples
Demonstrates how to use the relative_input_path parameter
to control output directory structure when processing PDFs.
"""

import requests
import json
from pathlib import Path

# API configuration
API_BASE_URL = "http://localhost:8000"

def upload_with_hierarchy(file_path: str, relative_input_path: str = None):
    """
    Upload a PDF file with optional hierarchy preservation
    
    Args:
        file_path: Path to the PDF file
        relative_input_path: Relative path to preserve in output structure
    
    Returns:
        Document ID if successful, None if failed
    """
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    # Prepare request
    files = {'file': open(file_path, 'rb')}
    data = {
        'language': 'vie',
        'enable_handwriting_detection': False
    }
    
    # Add relative path if specified
    if relative_input_path:
        data['relative_input_path'] = relative_input_path
        print(f"📁 Uploading {file_path} with hierarchy: {relative_input_path}")
    else:
        print(f"📁 Uploading {file_path} (default behavior)")
    
    try:
        response = requests.post(f"{API_BASE_URL}/documents/transform", files=files, data=data)
        files['file'].close()
        
        if response.status_code == 200:
            result = response.json()
            document_id = result['document_id']
            print(f"✅ Upload successful! Document ID: {document_id}")
            
            # Show expected output location
            filename_base = Path(file_path).stem
            if relative_input_path:
                expected_output = f"output/{relative_input_path}/{filename_base}/"
            else:
                expected_output = f"output/{filename_base}/"
            print(f"📂 Expected output location: {expected_output}")
            
            return document_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return None

def demonstrate_hierarchy_scenarios():
    """
    Demonstrate different hierarchy scenarios
    """
    
    print("🎯 API Output Hierarchy Enhancement Examples")
    print("=" * 50)
    
    # Example scenarios
    scenarios = [
        {
            "description": "Scenario 1: Same filename in different folders",
            "files": [
                {"path": "samples/legal/contract.pdf", "relative_path": "legal"},
                {"path": "samples/invoices/contract.pdf", "relative_path": "invoices"},
                {"path": "samples/reports/contract.pdf", "relative_path": "reports"}
            ]
        },
        {
            "description": "Scenario 2: Nested folder structure",
            "files": [
                {"path": "documents/legal/contract.pdf", "relative_path": "documents/legal"},
                {"path": "documents/invoices/invoice_001.pdf", "relative_path": "documents/invoices"},
                {"path": "documents/reports/monthly_report.pdf", "relative_path": "documents/reports"}
            ]
        },
        {
            "description": "Scenario 3: Default behavior (no hierarchy)",
            "files": [
                {"path": "samples/document.pdf", "relative_path": None}
            ]
        },
        {
            "description": "Scenario 4: Date-based organization",
            "files": [
                {"path": "samples/2024/01/report.pdf", "relative_path": "2024/01"},
                {"path": "samples/2024/02/report.pdf", "relative_path": "2024/02"}
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['description']}")
        print("-" * 40)
        
        for file_info in scenario['files']:
            file_path = file_info['path']
            relative_path = file_info['relative_path']
            
            # Note: This is just for demonstration
            # In practice, you would have actual files
            print(f"\n📄 File: {file_path}")
            if relative_path:
                print(f"🗂️  Relative path: {relative_path}")
                print(f"📂 Output will be: output/{relative_path}/{Path(file_path).stem}/")
            else:
                print(f"📂 Output will be: output/{Path(file_path).stem}/")
            
            # Uncomment the line below to actually upload (if files exist)
            # upload_with_hierarchy(file_path, relative_path)
    
    print("\n💡 Usage Tips:")
    print("1. Use relative_input_path to preserve folder structure")
    print("2. Leave relative_input_path empty for default behavior")
    print("3. The API automatically sanitizes paths for security")
    print("4. Output structure: output/[relative_path]/[filename]/")
    print("5. Perfect for batch processing with organized outputs")
    print("6. Supports nested directory structures")
    print("7. Handles files with identical names from different folders")

def show_api_usage_examples():
    """
    Show code examples for different programming languages
    """
    
    print("\n🔧 API Usage Examples")
    print("=" * 30)
    
    print("\n📝 Python (requests):")
    print("""
import requests

# Upload with hierarchy preservation
files = {'file': open('samples/folder1/document.pdf', 'rb')}
data = {
    'language': 'vie',
    'enable_handwriting_detection': False,
    'relative_input_path': 'folder1'  # NEW parameter
}

response = requests.post('http://localhost:8000/documents/transform', 
                        files=files, data=data)
result = response.json()
print(f"Document ID: {result['document_id']}")
""")
    
    print("\n📝 cURL:")
    print("""
# Upload with hierarchy preservation
curl -X POST "http://localhost:8000/documents/transform" \
  -F "file=@samples/folder1/document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false" \
  -F "relative_input_path=folder1"
""")
    
    print("\n📝 JavaScript (fetch):")
    print("""
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('language', 'vie');
formData.append('enable_handwriting_detection', 'false');
formData.append('relative_input_path', 'folder1'); // NEW parameter

fetch('http://localhost:8000/documents/transform', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log('Document ID:', data.document_id));
""")

def test_with_actual_files():
    """
    Test the hierarchy enhancement with actual sample files
    """
    import os
    
    # Check for sample files
    sample_files = ["samples/1.pdf", "samples/2.pdf"]
    available_files = [f for f in sample_files if os.path.exists(f)]
    
    if not available_files:
        print("❌ No sample files found. Please ensure sample PDF files exist in samples/ directory")
        return
    
    print(f"\n🧪 Testing with {len(available_files)} sample files")
    print("=" * 50)
    
    for i, file_path in enumerate(available_files):
        filename = Path(file_path).stem
        relative_path = f"test_batch_{i+1}"
        
        print(f"\n📄 Testing file: {file_path}")
        print(f"📁 Relative path: {relative_path}")
        print(f"📂 Expected output: output/{relative_path}/{filename}/")
        
        # Uncomment to actually test
        # result = upload_with_hierarchy(file_path, relative_path)
        # if result:
        #     print(f"✅ Success: {result}")
        # else:
        #     print("❌ Failed")
        
        print("(Uncomment the upload lines in test_with_actual_files() to run actual tests)")

if __name__ == "__main__":
    demonstrate_hierarchy_scenarios()
    show_api_usage_examples()
    test_with_actual_files()
    
    print("\n🚀 Ready to test!")
    print("Uncomment the upload lines in test_with_actual_files() to test with actual API calls")