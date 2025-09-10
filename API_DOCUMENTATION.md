# Case Management & OCR API Documentation

## Overview

This API provides a comprehensive case management and extraction workflow system built on top of the OCR API. It enables you to:

- Create and manage cases for document processing
- Add documents to cases (upload or URL)
- Coordinate OCR jobs across multiple cases
- Manage extraction workflows with leasing and status tracking
- Handle webhooks for job notifications
- Monitor system metrics and health

## Base URLs

- **Case Management API**: `http://localhost:8001`
- **OCR API**: `http://localhost:8000`

## Quick Start

### OCR API (Direct Processing)
For direct document processing without case management:

```bash
# Process a PDF document
curl -X POST "http://localhost:8000/documents/transform" \
  -F "file=@document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"

# Check processing status
curl -X GET "http://localhost:8000/documents/status/{document_id}"
```

### Case Management API (Workflow Processing)
For structured workflow with case management:

```bash
# Create case and add documents
curl -X POST "http://localhost:8001/v1/cases" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"name": "Document Processing Case"}'
```

## Authentication & Headers

### Required Headers

```http
Content-Type: application/json
Idempotency-Key: <unique-uuid>  # Required for POST/PATCH requests
```

### Optional Headers

```http
Authorization: Bearer <token>  # For future authentication
X-Request-ID: <uuid>          # For request tracing
```

## Core Concepts

### Case Lifecycle

1. **Created** → Case is created with documents
2. **Processing** → OCR jobs are running
3. **Ready for Extraction** → OCR completed, ready for data extraction
4. **Extraction In Progress** → Being processed by extraction worker
5. **Completed** → Extraction finished successfully
6. **Failed** → Processing or extraction failed

### Extraction Workflow

The extraction workflow uses a **lease-based system** to prevent duplicate work:

1. **Claim**: Get cases ready for extraction with a lease
2. **Process**: Update status to `in_progress`
3. **Complete**: Update status to `succeeded` or `failed`
4. **Release**: Lease expires automatically or is released

## API Endpoints

### 1. Case Management

#### Create Case

```bash
curl -X POST "http://localhost:8001/v1/cases" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "name": "Legal Document Case",
    "description": "Processing Vietnamese court decision",
    "metadata": {"client": "ABC Law Firm", "priority": "high"},
    "priority": 8
  }'
```

**Response:**
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Legal Document Case",
  "description": "Processing Vietnamese court decision",
  "status": "created",
  "priority": 8,
  "metadata": {"client": "ABC Law Firm", "priority": "high"},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Get Case Details

```bash
curl -X GET "http://localhost:8001/v1/cases/{case_id}"
```

#### Update Case

```bash
curl -X PATCH "http://localhost:8001/v1/cases/{case_id}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "description": "Updated description",
    "metadata": {"updated": true}
  }'
```

#### List Cases

```bash
curl -X GET "http://localhost:8001/v1/cases?status=created&limit=10&cursor=abc123"
```

### 2. Document Management

#### Add Document to Case

```bash
curl -X POST "http://localhost:8001/v1/cases/{case_id}/documents" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "filename": "court_decision.pdf",
    "url": "https://example.com/documents/court_decision.pdf",
    "metadata": {"pages": 4, "language": "vietnamese"}
  }'
```

**Response:**
```json
{
  "document_id": "doc_123456",
  "filename": "court_decision.pdf",
  "url": "https://example.com/documents/court_decision.pdf",
  "status": "uploaded",
  "metadata": {"pages": 4, "language": "vietnamese"},
  "created_at": "2024-01-15T10:35:00Z"
}
```

#### List Case Documents

```bash
curl -X GET "http://localhost:8001/v1/cases/{case_id}/documents"
```

### 3. Job Management

#### Create OCR Job

```bash
curl -X POST "http://localhost:8001/v1/jobs" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "case_ids": ["case_id_1", "case_id_2"],
    "language": "vie",
    "enable_handwriting_detection": false,
    "priority": 7
  }'
```

**Response:**
```json
{
  "job_id": "job_789012",
  "case_ids": ["case_id_1", "case_id_2"],
  "status": "pending",
  "language": "vie",
  "enable_handwriting_detection": false,
  "priority": 7,
  "created_at": "2024-01-15T10:40:00Z",
  "estimated_completion": "2024-01-15T10:45:00Z"
}
```

#### Get Job Status

```bash
curl -X GET "http://localhost:8001/v1/jobs/{job_id}"
```

#### List Jobs

```bash
curl -X GET "http://localhost:8001/v1/jobs?status=pending&limit=10"
```

### 4. Extraction Workflow

#### Get Cases Ready for Extraction

**Without claiming (just check):**
```bash
curl -X GET "http://localhost:8001/v1/cases/ready-for-extraction?claim=false&limit=5"
```

**With claiming (lease for processing):**
```bash
curl -X GET "http://localhost:8001/v1/cases/ready-for-extraction?claim=true&lease_duration_minutes=30&limit=5"
```

**Response:**
```json
{
  "cases": [
    {
      "case_id": "case_123",
      "name": "Legal Document Case",
      "documents_count": 2,
      "priority": 8,
      "ready_since": "2024-01-15T10:45:00Z"
    }
  ],
  "claimed": 1,
  "lease_expires_at": "2024-01-15T11:15:00Z"
}
```

#### Update Extraction Status

```bash
curl -X PATCH "http://localhost:8001/v1/cases/{case_id}/extraction-status" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "status": "in_progress",
    "metadata": {"worker_id": "worker_001", "started_at": "2024-01-15T10:50:00Z"}
  }'
```

#### Extend Lease

```bash
curl -X PATCH "http://localhost:8001/v1/cases/{case_id}/lease/extend" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "duration_minutes": 45
  }'
```

#### Bulk Update Extraction Status

```bash
curl -X PATCH "http://localhost:8001/v1/cases/extraction-status/bulk" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "updates": [
      {
        "case_id": "case_1",
        "status": "succeeded",
        "metadata": {"entities_extracted": 15}
      },
      {
        "case_id": "case_2",
        "status": "failed",
        "metadata": {"error": "Invalid document format"}
      }
    ]
  }'
```

### 5. Webhook System

#### Send Test Webhook

```bash
curl -X POST "http://localhost:8001/v1/webhooks/test" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "event_type": "job.completed",
    "timestamp": "2024-01-15T11:00:00Z",
    "data": {
      "job_id": "job_123",
      "case_ids": ["case_456"],
      "status": "completed",
      "processing_time": 10.5
    }
  }'
```

#### Get Webhook History

```bash
curl -X GET "http://localhost:8001/v1/webhooks/history?limit=10"
```

### 6. Monitoring & Metrics

#### Health Check

```bash
curl -X GET "http://localhost:8001/v1/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T11:05:00Z",
  "version": "1.0.0",
  "stats": {
    "total_cases": 150,
    "total_jobs": 75,
    "active_leases": 5
  }
}
```

## OCR API Endpoints

### Direct Document Processing

#### Process PDF Document

```bash
curl -X POST "http://localhost:8000/documents/transform" \
  -F "file=@samples/document.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"
```

**Alternative with URL:**
```bash
curl -X POST "http://localhost:8000/documents/transform" \
  -F 'url_data={"url":"https://example.com/document.pdf","filename":"document.pdf"}' \
  -F "language=vie"
```

**Parameters:**
- `file` (optional): PDF file upload
- `url_data` (optional): JSON string with URL and filename
- `language` (default: "vie"): OCR language code (vie, eng, vie+eng)
- `enable_handwriting_detection` (default: false): Enable handwriting detection

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "processing_time": 11.05,
  "total_pages": 4,
  "issues_detected": false,
  "quality_issues": [],
  "pages": [
    {
      "page_number": 1,
      "pdf_file": "pdf/1_page1.pdf",
      "text_file": "text/1_page1.txt",
      "quality_analysis": {
        "file_size_bytes": 245760,
        "rotation_detected": false,
        "is_blank": false,
        "skew_detected": false,
        "handwriting_detected": false,
        "issues": []
      },
      "extracted_text": "MỤC LUC Hồ SƠ...",
      "issues": []
    }
  ],
  "output_directory": "output/1"
}
```

#### Check Document Status

```bash
curl -X GET "http://localhost:8000/documents/status/{document_id}"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "Processing completed successfully",
  "result": {
    "processing_time": 11.05,
    "total_pages": 4,
    "output_directory": "output/1"
  }
}
```

#### Health Check

```bash
curl -X GET "http://localhost:8000/"
```

**Response:**
```json
{
  "status": "healthy",
  "message": "OCR API is running"
}
```

### Quality Analysis Features

The OCR API automatically detects and reports:

1. **Rotation Detection**: Identifies pages that need rotation
2. **Skew Detection**: Detects tilted or skewed pages
3. **Blank Page Detection**: Identifies pages with minimal content
4. **Handwriting Detection**: Optional detection of handwritten content
5. **File Size Analysis**: Identifies unusually small or large files
6. **Text Extraction Confidence**: Quality metrics for OCR results

### Supported Languages

- `vie`: Vietnamese (primary)
- `eng`: English
- `vie+eng`: Vietnamese + English (multilingual)
- Additional languages available via Tesseract

### Performance Metrics

Based on recent testing:
- **Average Processing Speed**: ~1.2 seconds per page
- **Success Rate**: 100% (4/4 files in latest test)
- **Supported File Sizes**: Up to 18MB+ PDFs
- **Concurrent Processing**: Up to 16 parallel workers
- **Memory Efficiency**: In-memory processing with large file support

#### System Metrics

```bash
curl -X GET "http://localhost:8001/v1/metrics"
```

**Response:**
```json
{
  "case_statuses": {
    "created": 25,
    "processing": 10,
    "ready_for_extraction": 5,
    "completed": 110
  },
  "job_statuses": {
    "pending": 3,
    "running": 2,
    "completed": 70
  },
  "extraction_statuses": {
    "pending": 5,
    "in_progress": 2,
    "succeeded": 108,
    "failed": 5
  },
  "performance": {
    "avg_processing_time": 12.5,
    "avg_extraction_time": 3.2
  }
}
```

## Python SDK Examples

### Setup

```python
import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8001"
session = requests.Session()

def make_request(method, endpoint, **kwargs):
    url = f"{BASE_URL}{endpoint}"
    if method.upper() in ["POST", "PATCH"]:
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Idempotency-Key"] = str(uuid.uuid4())
    return session.request(method, url, **kwargs)
```

### Complete Workflow Example

```python
# 1. Create a case
case_data = {
    "name": "Legal Document Processing",
    "description": "Vietnamese court decision analysis",
    "metadata": {"client": "Law Firm XYZ", "urgent": True},
    "priority": 8
}

response = make_request("POST", "/v1/cases", json=case_data)
case = response.json()
case_id = case["case_id"]
print(f"Created case: {case_id}")

# 2. Add document to case
doc_data = {
    "filename": "legal_doc.pdf",
    "url": "https://example.com/docs/legal_doc.pdf",
    "metadata": {"pages": 4, "language": "vie"}
}

response = make_request("POST", f"/v1/cases/{case_id}/documents", json=doc_data)
document = response.json()
print(f"Added document: {document['document_id']}")

# 3. Create OCR job
job_data = {
    "case_ids": [case_id],
    "language": "vie",
    "enable_handwriting_detection": False,
    "priority": 7
}

response = make_request("POST", "/v1/jobs", json=job_data)
job = response.json()
job_id = job["job_id"]
print(f"Created job: {job_id}")

# 4. Poll job status
import time
while True:
    response = make_request("GET", f"/v1/jobs/{job_id}")
    job_status = response.json()
    
    if job_status["status"] == "completed":
        print("Job completed successfully!")
        break
    elif job_status["status"] == "failed":
        print("Job failed!")
        break
    
    print(f"Job status: {job_status['status']}")
    time.sleep(5)

# 5. Get cases ready for extraction
response = make_request("GET", "/v1/cases/ready-for-extraction", 
                       params={"claim": True, "lease_duration_minutes": 30})
ready_cases = response.json()

# 6. Process extraction
for case in ready_cases["cases"]:
    case_id = case["case_id"]
    
    # Start extraction
    update_data = {
        "status": "in_progress",
        "metadata": {"worker_id": "worker_001"}
    }
    make_request("PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data)
    
    # Simulate extraction work
    print(f"Processing case {case_id}...")
    time.sleep(2)
    
    # Complete extraction
    update_data = {
        "status": "succeeded",
        "metadata": {"entities": 15, "confidence": 0.95}
    }
    make_request("PATCH", f"/v1/cases/{case_id}/extraction-status", json=update_data)
    print(f"Completed extraction for case {case_id}")
```

## Best Practices

### 1. Idempotency

**Always use idempotency keys** for POST and PATCH requests to prevent duplicate operations:

```python
headers = {
    "Content-Type": "application/json",
    "Idempotency-Key": str(uuid.uuid4())
}
```

### 2. Leasing Strategy

**Use claim=true with appropriate lease duration:**

```python
# For short extractions (< 30 minutes)
params = {"claim": True, "lease_duration_minutes": 30}

# For long extractions (< 2 hours)
params = {"claim": True, "lease_duration_minutes": 120}
```

**Extend leases for long-running processes:**

```python
# Extend lease before it expires
extension_data = {"duration_minutes": 60}
make_request("PATCH", f"/v1/cases/{case_id}/lease/extend", json=extension_data)
```

### 3. Pagination

**Use cursor-based pagination for scalability:**

```python
# First page
response = make_request("GET", "/v1/cases", params={"limit": 50})
cases = response.json()

# Next page
if cases.get("next_cursor"):
    response = make_request("GET", "/v1/cases", 
                           params={"limit": 50, "cursor": cases["next_cursor"]})
```

### 4. Error Handling

**Implement proper retry logic:**

```python
import time
from requests.exceptions import RequestException

def make_request_with_retry(method, endpoint, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            response = make_request(method, endpoint, **kwargs)
            if response.status_code < 500:  # Don't retry client errors
                return response
        except RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

### 5. Monitoring

**Monitor key metrics:**

```python
def check_system_health():
    response = make_request("GET", "/v1/health")
    health = response.json()
    
    if health["status"] != "healthy":
        alert("System unhealthy!")
    
    # Check queue sizes
    response = make_request("GET", "/v1/metrics")
    metrics = response.json()
    
    pending_jobs = metrics["job_statuses"]["pending"]
    if pending_jobs > 100:
        alert(f"High job queue: {pending_jobs} pending jobs")
```

### 6. Webhook Handling

**Parse webhook payloads properly:**

```python
def handle_webhook(payload):
    event_type = payload.get("event_type")
    data = payload.get("data", {})
    
    if event_type == "job.completed":
        job_id = data["job_id"]
        case_ids = data["case_ids"]
        
        # Update case statuses to ready for extraction
        for case_id in case_ids:
            update_case_status(case_id, "ready_for_extraction")
    
    elif event_type == "job.failed":
        job_id = data["job_id"]
        error = data.get("error", "Unknown error")
        
        # Handle job failure
        handle_job_failure(job_id, error)
```

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 400 | Bad Request | Check request format and required fields |
| 401 | Unauthorized | Provide valid authentication |
| 404 | Not Found | Verify resource ID exists |
| 409 | Conflict | Check idempotency key or resource state |
| 422 | Validation Error | Fix validation errors in request |
| 429 | Rate Limited | Implement backoff and retry |
| 500 | Server Error | Retry with exponential backoff |

## Rate Limits

- **General API**: 1000 requests/minute per client
- **Job Creation**: 100 jobs/minute per client
- **Webhook Endpoints**: 500 requests/minute per client

## Security Considerations

1. **Always use HTTPS** in production
2. **Validate webhook signatures** to prevent spoofing
3. **Implement proper authentication** for sensitive operations
4. **Use secure file URLs** with expiration times
5. **Sanitize metadata** to prevent injection attacks

## Performance Tips

1. **Batch operations** when possible (bulk updates)
2. **Use appropriate page sizes** (50-100 items)
3. **Implement connection pooling** for high-volume clients
4. **Cache frequently accessed data** (case details, job statuses)
5. **Monitor lease expiration** to avoid stale locks

## Support

For technical support or questions:
- API Documentation: `/docs` endpoint
- Health Check: `/v1/health`
- Metrics: `/v1/metrics`
- Integration Tests: Run `python integration_test.py`

---

*This documentation covers the complete Case Management & OCR API. For the latest updates, check the interactive API documentation at `http://localhost:8001/docs`.*