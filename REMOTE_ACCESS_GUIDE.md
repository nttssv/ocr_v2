# 🌐 Remote Access Guide for OCR API

This guide shows you how to access your OCR API from your local computer.

## 🔧 Current API Configuration

- **OCR API**: http://localhost:8000 (Primary API - Fully Operational)
- **Case Management API**: http://localhost:8001 (Available but may require setup)
- **Status**: ✅ Running
- **Performance**: ~1.1 seconds per page processing

## 🚀 Method 1: Direct Access (If API is accessible)

### Step 1: Test API Accessibility

From your local computer, test if the API is accessible (replace with actual IP):

```bash
# Test API health
curl http://[YOUR_SERVER_IP]:8000/health

# Test API info
curl http://[YOUR_SERVER_IP]:8000/
```

### Step 2: Process a Document

```bash
# Upload and process a PDF
curl -X POST "http://10.148.0.2:8000/documents/transform" \
  -F "file=@your_document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"
```

### Step 3: Check Processing Status

```bash
# Replace DOCUMENT_ID with the ID returned from upload
curl "http://10.148.0.2:8000/documents/status/DOCUMENT_ID"
```

## 🔒 Method 2: SSH Tunnel (Recommended for Security)

If direct access doesn't work, use SSH tunneling:

### Step 1: Create SSH Tunnel

From your local computer, run (replace with your server details):

```bash
# Create SSH tunnel to forward local port 8000 to remote port 8000
ssh -L 8000:localhost:8000 user@[YOUR_SERVER_IP]

# Or if you have a different SSH port:
ssh -L 8000:localhost:8000 -p YOUR_SSH_PORT user@[YOUR_SERVER_IP]
```

### Step 2: Access API Locally

Once the tunnel is established, access the API as if it's running locally:

```bash
# Test API health
curl http://localhost:8000/health

# Process a document
curl -X POST "http://localhost:8000/documents/transform" \
  -F "file=@your_document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"
```

## 🌍 Method 3: Public Access (Production Setup)

For production use, you'll need to configure the API for public access:

### Step 1: Update API Configuration

Modify the API to bind to all interfaces:

```python
# In api.py, change the uvicorn.run line to:
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Configure Firewall

```bash
# Allow port 8000 through firewall
sudo ufw allow 8000
```

### Step 3: Access via Public IP

```bash
# Use your server's public IP
curl http://YOUR_PUBLIC_IP:8000/health
```

## 🐍 Python Client Examples

### Basic Python Client

```python
import requests
import json

# API base URL
API_URL = "http://10.148.0.2:8000"  # or localhost:8000 for SSH tunnel

def test_api():
    # Test health
    response = requests.get(f"{API_URL}/health")
    print("Health:", response.json())
    
    # Test info
    response = requests.get(f"{API_URL}/")
    print("Info:", response.json())

def process_document(file_path, language="vie"):
    # Upload document
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'language': language,
            'enable_handwriting_detection': 'false'
        }
        
        response = requests.post(
            f"{API_URL}/documents/transform",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        document_id = result['document_id']
        print(f"Document uploaded: {document_id}")
        
        # Check status
        while True:
            status_response = requests.get(f"{API_URL}/documents/status/{document_id}")
            status_data = status_response.json()
            
            print(f"Status: {status_data['status']}, Progress: {status_data['progress']}")
            
            if status_data['status'] == 'completed':
                print("Processing completed!")
                print(json.dumps(status_data['result'], indent=2))
                break
            elif status_data['status'] == 'failed':
                print("Processing failed!")
                break
            
            time.sleep(5)
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Usage
if __name__ == "__main__":
    test_api()
    process_document("your_document.pdf")
```

### Advanced Python Client

```python
import requests
import time
import json
from pathlib import Path

class OCRClient:
    def __init__(self, base_url="http://10.148.0.2:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json() if response.status_code == 200 else None
    
    def process_document(self, file_path, language="vie", enable_handwriting=False):
        """Process a document and return results"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
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
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        document_id = response.json()['document_id']
        print(f"Document uploaded: {document_id}")
        
        # Wait for completion
        return self.wait_for_completion(document_id)
    
    def wait_for_completion(self, document_id, max_wait=300):
        """Wait for document processing to complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.session.get(f"{self.base_url}/documents/status/{document_id}")
            data = response.json()
            
            status = data['status']
            progress = data['progress']
            
            print(f"Status: {status}, Progress: {progress:.2f}")
            
            if status == 'completed':
                return data['result']
            elif status == 'failed':
                raise Exception(f"Processing failed: {data.get('error', 'Unknown error')}")
            
            time.sleep(5)
        
        raise Exception("Processing timeout")

# Usage
if __name__ == "__main__":
    client = OCRClient()
    
    # Check health
    health = client.health_check()
    print("API Health:", health)
    
    # Process document
    try:
        result = client.process_document("your_document.pdf", language="vie")
        print("Processing completed!")
        print(f"Pages processed: {result['total_pages']}")
        print(f"Processing time: {result['processing_time']}s")
    except Exception as e:
        print(f"Error: {e}")
```

## 🌐 Web Browser Access

You can also access the API through a web browser:

### API Documentation
- **Swagger UI**: `http://10.148.0.2:8000/docs`
- **ReDoc**: `http://10.148.0.2:8000/redoc`

### Health Check
- **Health**: `http://10.148.0.2:8000/health`
- **Info**: `http://10.148.0.2:8000/`

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if API is running: `ps aux | grep "python api.py"`
   - Check firewall settings
   - Verify IP address and port

2. **SSH Tunnel Issues**
   - Ensure SSH access to the server
   - Check if port 8000 is available locally
   - Verify tunnel is established: `netstat -an | grep 8000`

3. **File Upload Issues**
   - Check file size limits
   - Verify file format (PDF only)
   - Ensure proper MIME type

### Debug Commands

```bash
# Check if API is running
ps aux | grep "python api.py"

# Check port usage
netstat -tlnp | grep 8000

# Test local connectivity
telnet 10.148.0.2 8000

# Check API logs
tail -f /path/to/api/logs
```

## 📱 Mobile/App Integration

### cURL Examples for Mobile Apps

```bash
# Health check
curl -X GET "http://10.148.0.2:8000/health" \
  -H "Accept: application/json"

# Upload document
curl -X POST "http://10.148.0.2:8000/documents/transform" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"

# Check status
curl -X GET "http://10.148.0.2:8000/documents/status/DOCUMENT_ID" \
  -H "Accept: application/json"
```

## 🚀 Quick Start Commands

### Test API from Your Computer

```bash
# 1. Test health
curl http://10.148.0.2:8000/health

# 2. Upload a document
curl -X POST "http://10.148.0.2:8000/documents/transform" \
  -F "file=@your_document.pdf" \
  -F "language=vie"

# 3. Check status (replace DOCUMENT_ID)
curl http://10.148.0.2:8000/documents/status/DOCUMENT_ID
```

### Using SSH Tunnel

```bash
# 1. Create tunnel
ssh -L 8000:localhost:8000 gcpcoder@YOUR_SERVER_IP

# 2. In another terminal, test locally
curl http://localhost:8000/health
```

## 📞 Support

If you encounter issues:

1. Check the API logs on the server
2. Verify network connectivity
3. Test with the integration test suite
4. Check firewall and security group settings

---

**Ready to use your OCR API from anywhere!** 🎉
