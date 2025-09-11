"""
Case Management and Extraction Workflow API Extension
Extends the existing OCR API with comprehensive case management, job coordination, and extraction workflows.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import (
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

# Configure logging
logger = logging.getLogger(__name__)


# Enums for status management
class CaseStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    READY_FOR_EXTRACTION = "ready_for_extraction"
    IN_EXTRACTION = "in_extraction"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STALE = "stale"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Pydantic Models
class DocumentCreate(BaseModel):
    """Model for creating a document within a case"""

    filename: str
    url: Optional[str] = None  # Changed from HttpUrl to str to accept file:// URLs
    metadata: Optional[Dict[str, Any]] = {}


class DocumentResponse(BaseModel):
    """Document response model"""

    document_id: str
    case_id: str
    filename: str
    status: DocumentStatus
    url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    ocr_result: Optional[Dict[str, Any]] = None


class CaseCreate(BaseModel):
    """Model for creating a new case"""

    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = Field(default=5, ge=1, le=10)


class CaseResponse(BaseModel):
    """Case response model"""

    case_id: str
    name: str
    description: Optional[str] = None
    status: CaseStatus
    metadata: Dict[str, Any] = {}
    priority: int
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []
    extraction_status: Optional[ExtractionStatus] = None
    lease_expires_at: Optional[datetime] = None
    lease_holder: Optional[str] = None


class JobCreate(BaseModel):
    """Model for creating OCR jobs"""

    case_ids: List[str]
    language: Optional[str] = "vie"
    enable_handwriting_detection: Optional[bool] = False
    priority: Optional[int] = Field(default=5, ge=1, le=10)


class JobResponse(BaseModel):
    """Job response model"""

    job_id: str
    case_ids: List[str]
    status: JobStatus
    language: str
    enable_handwriting_detection: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExtractionUpdate(BaseModel):
    """Model for updating extraction status"""

    status: ExtractionStatus
    metadata: Optional[Dict[str, Any]] = {}
    error_message: Optional[str] = None


class BulkExtractionUpdate(BaseModel):
    """Model for bulk extraction status updates"""

    updates: List[Dict[str, Union[str, ExtractionStatus, Dict[str, Any]]]]


class WebhookPayload(BaseModel):
    """Webhook payload model"""

    event_type: str  # "job.completed", "job.failed", "case.ready_for_extraction"
    timestamp: datetime
    data: Dict[str, Any]


class PaginationParams(BaseModel):
    """Pagination parameters"""

    cursor: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=1000)


class LeaseExtension(BaseModel):
    """Model for extending leases"""

    duration_minutes: int = Field(default=30, ge=1, le=1440)


# In-memory storage (replace with database in production)
cases_db: Dict[str, Dict[str, Any]] = {}
documents_db: Dict[str, Dict[str, Any]] = {}
jobs_db: Dict[str, Dict[str, Any]] = {}
webhooks_db: List[Dict[str, Any]] = []


# Utility functions
def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """Get current timestamp"""
    return datetime.utcnow()


def validate_idempotency_key(idempotency_key: Optional[str] = Header(None)) -> str:
    """Validate and return idempotency key or generate a default one"""
    if not idempotency_key:
        # Generate a default idempotency key based on timestamp and random value
        import random
        import time

        idempotency_key = f"auto-{int(time.time())}-{random.randint(1000, 9999)}"
    return idempotency_key


def create_cursor(timestamp: datetime, id: str) -> str:
    """Create a cursor for pagination"""
    cursor_data = f"{timestamp.isoformat()}:{id}"
    return hashlib.md5(cursor_data.encode()).hexdigest()


def parse_cursor(cursor: str) -> Optional[datetime]:
    """Parse cursor to extract timestamp"""
    try:
        # In production, implement proper cursor decoding
        return None
    except:
        return None


# Create FastAPI app extension
case_app = FastAPI(
    title="Case Management & Extraction API",
    description="Extended API for case management, job coordination, and extraction workflows",
    version="2.0.0",
)

# Add CORS middleware
case_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Case Management Endpoints
@case_app.post("/v1/cases", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate, idempotency_key: str = Depends(validate_idempotency_key)
):
    """
    Create a new case for document processing.

    - **name**: Case name (required)
    - **description**: Optional case description
    - **metadata**: Additional metadata as key-value pairs
    - **priority**: Priority level (1-10, default: 5)
    """
    case_id = generate_id()
    timestamp = get_current_timestamp()

    case = {
        "case_id": case_id,
        "name": case_data.name,
        "description": case_data.description,
        "status": CaseStatus.CREATED,
        "metadata": case_data.metadata or {},
        "priority": case_data.priority,
        "created_at": timestamp,
        "updated_at": timestamp,
        "documents": [],
        "extraction_status": ExtractionStatus.PENDING,
        "lease_expires_at": None,
        "lease_holder": None,
    }

    cases_db[case_id] = case

    return CaseResponse(**case)


@case_app.get("/v1/cases/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    """Get case details by ID"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]

    # Get associated documents
    case_documents = [
        DocumentResponse(**doc)
        for doc in documents_db.values()
        if doc["case_id"] == case_id
    ]

    case_response = CaseResponse(**case)
    case_response.documents = case_documents

    return case_response


@case_app.get("/v1/cases", response_model=Dict[str, Any])
async def list_cases(
    status: Optional[CaseStatus] = None,
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    """
    List cases with optional filtering and cursor-based pagination.

    - **status**: Filter by case status
    - **cursor**: Pagination cursor
    - **limit**: Number of results per page (1-1000)
    """
    filtered_cases = []

    for case in cases_db.values():
        if status and case["status"] != status:
            continue
        filtered_cases.append(case)

    # Sort by created_at descending
    filtered_cases.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply pagination
    start_idx = 0
    if cursor:
        # In production, implement proper cursor-based pagination
        pass

    paginated_cases = filtered_cases[start_idx : start_idx + limit]

    # Generate next cursor
    next_cursor = None
    if len(paginated_cases) == limit and start_idx + limit < len(filtered_cases):
        last_case = paginated_cases[-1]
        next_cursor = create_cursor(last_case["created_at"], last_case["case_id"])

    return {
        "cases": [CaseResponse(**case) for case in paginated_cases],
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
            "total_count": len(filtered_cases),
        },
    }


@case_app.patch("/v1/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    updates: Dict[str, Any],
    idempotency_key: str = Depends(validate_idempotency_key),
):
    """Update case details"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]

    # Update allowed fields
    allowed_fields = ["name", "description", "metadata", "priority"]
    for field, value in updates.items():
        if field in allowed_fields:
            case[field] = value

    case["updated_at"] = get_current_timestamp()

    return CaseResponse(**case)


# Document Management Endpoints
@case_app.post("/v1/cases/{case_id}/documents", response_model=DocumentResponse)
async def add_document_to_case(
    case_id: str,
    document_data: DocumentCreate,
    idempotency_key: str = Depends(validate_idempotency_key),
):
    """
    Add a document to a case.

    - **filename**: Document filename
    - **url**: Optional URL for document download
    - **metadata**: Additional document metadata
    """
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    document_id = generate_id()
    timestamp = get_current_timestamp()

    document = {
        "document_id": document_id,
        "case_id": case_id,
        "filename": document_data.filename,
        "status": DocumentStatus.UPLOADED,
        "url": document_data.url,
        "metadata": document_data.metadata or {},
        "created_at": timestamp,
        "updated_at": timestamp,
        "ocr_result": None,
    }

    documents_db[document_id] = document

    # Update case status
    cases_db[case_id]["updated_at"] = timestamp

    return DocumentResponse(**document)


@case_app.get("/v1/cases/{case_id}/documents", response_model=List[DocumentResponse])
async def list_case_documents(case_id: str):
    """List all documents in a case"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case_documents = [
        DocumentResponse(**doc)
        for doc in documents_db.values()
        if doc["case_id"] == case_id
    ]

    return case_documents


# Job Management Endpoints
@case_app.post("/v1/jobs", response_model=JobResponse)
async def create_ocr_job(
    job_data: JobCreate, idempotency_key: str = Depends(validate_idempotency_key)
):
    """
    Create an OCR job for one or more cases.

    - **case_ids**: List of case IDs to process
    - **language**: OCR language (default: 'vie')
    - **enable_handwriting_detection**: Enable handwriting detection
    - **priority**: Job priority (1-10)
    """
    # Validate case IDs
    for case_id in job_data.case_ids:
        if case_id not in cases_db:
            raise HTTPException(status_code=400, detail=f"Case {case_id} not found")

    job_id = generate_id()
    timestamp = get_current_timestamp()

    job = {
        "job_id": job_id,
        "case_ids": job_data.case_ids,
        "status": JobStatus.PENDING,
        "language": job_data.language,
        "enable_handwriting_detection": job_data.enable_handwriting_detection,
        "priority": job_data.priority,
        "created_at": timestamp,
        "updated_at": timestamp,
        "started_at": None,
        "completed_at": None,
        "progress": 0.0,
        "results": None,
        "error": None,
    }

    jobs_db[job_id] = job

    # Update case statuses
    for case_id in job_data.case_ids:
        cases_db[case_id]["status"] = CaseStatus.PROCESSING
        cases_db[case_id]["updated_at"] = timestamp

    return JobResponse(**job)


@case_app.get("/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get job status and details"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(**jobs_db[job_id])


@case_app.get("/v1/jobs", response_model=Dict[str, Any])
async def list_jobs(
    status: Optional[JobStatus] = None,
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    """List jobs with optional filtering and pagination"""
    filtered_jobs = []

    for job in jobs_db.values():
        if status and job["status"] != status:
            continue
        filtered_jobs.append(job)

    # Sort by created_at descending
    filtered_jobs.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply pagination (simplified)
    paginated_jobs = filtered_jobs[:limit]

    return {
        "jobs": [JobResponse(**job) for job in paginated_jobs],
        "pagination": {
            "next_cursor": None,
            "has_more": False,
            "total_count": len(filtered_jobs),
        },
    }


@case_app.patch("/v1/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str, idempotency_key: str = Depends(validate_idempotency_key)
):
    """Cancel a running job"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[job_id]

    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")

    job["status"] = JobStatus.CANCELLED
    job["updated_at"] = get_current_timestamp()

    return {"message": "Job cancelled successfully"}


# Extraction Workflow Endpoints
@case_app.get("/v1/cases/ready-for-extraction", response_model=Dict[str, Any])
async def get_cases_ready_for_extraction(
    claim: bool = Query(default=False),
    lease_duration_minutes: int = Query(default=30, ge=1, le=1440),
    limit: int = Query(default=10, ge=1, le=100),
):
    """
    Get cases ready for extraction with optional claiming/leasing.

    - **claim**: Whether to claim cases with a lease
    - **lease_duration_minutes**: Lease duration (1-1440 minutes)
    - **limit**: Maximum number of cases to return
    """
    ready_cases = []
    current_time = get_current_timestamp()

    for case in cases_db.values():
        # Check if case is ready for extraction
        if case["status"] != CaseStatus.READY_FOR_EXTRACTION:
            continue

        # Check if lease is expired or not claimed
        if case["lease_expires_at"] and case["lease_expires_at"] > current_time:
            continue

        ready_cases.append(case)

    # Sort by priority (higher first) then by created_at
    ready_cases.sort(key=lambda x: (-x["priority"], x["created_at"]))

    # Limit results
    ready_cases = ready_cases[:limit]

    # Claim cases if requested
    if claim and ready_cases:
        lease_holder = generate_id()  # In production, use authenticated user ID
        lease_expires_at = current_time + timedelta(minutes=lease_duration_minutes)

        for case in ready_cases:
            case["status"] = CaseStatus.IN_EXTRACTION
            case["extraction_status"] = ExtractionStatus.IN_PROGRESS
            case["lease_holder"] = lease_holder
            case["lease_expires_at"] = lease_expires_at
            case["updated_at"] = current_time

    return {
        "cases": [CaseResponse(**case) for case in ready_cases],
        "claimed": claim,
        "lease_expires_at": (
            ready_cases[0]["lease_expires_at"] if claim and ready_cases else None
        ),
    }


@case_app.patch("/v1/cases/{case_id}/extraction-status", response_model=CaseResponse)
async def update_extraction_status(
    case_id: str,
    update_data: ExtractionUpdate,
    idempotency_key: str = Depends(validate_idempotency_key),
):
    """
    Update extraction status for a case.

    - **status**: New extraction status
    - **metadata**: Additional metadata
    - **error_message**: Error message if status is 'failed'
    """
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]
    current_time = get_current_timestamp()

    # Update extraction status
    case["extraction_status"] = update_data.status
    case["updated_at"] = current_time

    if update_data.metadata:
        case["metadata"].update(update_data.metadata)

    # Update case status based on extraction status
    if update_data.status == ExtractionStatus.SUCCEEDED:
        case["status"] = CaseStatus.COMPLETED
        case["lease_expires_at"] = None
        case["lease_holder"] = None
    elif update_data.status == ExtractionStatus.FAILED:
        case["status"] = CaseStatus.FAILED
        if update_data.error_message:
            case["metadata"]["error_message"] = update_data.error_message

    return CaseResponse(**case)


@case_app.patch("/v1/cases/extraction-status/bulk")
async def bulk_update_extraction_status(
    updates: BulkExtractionUpdate,
    idempotency_key: str = Depends(validate_idempotency_key),
):
    """Bulk update extraction statuses for multiple cases"""
    results = []
    current_time = get_current_timestamp()

    for update in updates.updates:
        case_id = update.get("case_id")
        status = update.get("status")
        metadata = update.get("metadata", {})

        if case_id not in cases_db:
            results.append(
                {"case_id": case_id, "success": False, "error": "Case not found"}
            )
            continue

        case = cases_db[case_id]
        case["extraction_status"] = status
        case["updated_at"] = current_time

        if metadata:
            case["metadata"].update(metadata)

        results.append({"case_id": case_id, "success": True})

    return {"results": results}


@case_app.patch("/v1/cases/{case_id}/lease/extend")
async def extend_lease(
    case_id: str,
    extension: LeaseExtension,
    idempotency_key: str = Depends(validate_idempotency_key),
):
    """Extend the lease on a case"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]
    current_time = get_current_timestamp()

    if not case["lease_expires_at"] or case["lease_expires_at"] <= current_time:
        raise HTTPException(status_code=400, detail="No active lease to extend")

    # Extend lease
    case["lease_expires_at"] = current_time + timedelta(
        minutes=extension.duration_minutes
    )
    case["updated_at"] = current_time

    return {
        "message": "Lease extended successfully",
        "new_expiry": case["lease_expires_at"],
    }


@case_app.patch("/v1/cases/{case_id}/lease/release")
async def release_lease(
    case_id: str, idempotency_key: str = Depends(validate_idempotency_key)
):
    """Release the lease on a case"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]

    # Release lease
    case["lease_expires_at"] = None
    case["lease_holder"] = None
    case["status"] = CaseStatus.READY_FOR_EXTRACTION
    case["extraction_status"] = ExtractionStatus.PENDING
    case["updated_at"] = get_current_timestamp()

    return {"message": "Lease released successfully"}


@case_app.patch("/v1/cases/{case_id}/reopen")
async def reopen_case(
    case_id: str, idempotency_key: str = Depends(validate_idempotency_key)
):
    """Reopen a case for re-extraction"""
    if case_id not in cases_db:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_db[case_id]

    # Reopen case
    case["status"] = CaseStatus.READY_FOR_EXTRACTION
    case["extraction_status"] = ExtractionStatus.PENDING
    case["lease_expires_at"] = None
    case["lease_holder"] = None
    case["updated_at"] = get_current_timestamp()

    return {"message": "Case reopened successfully"}


# Webhook Endpoints
@case_app.post("/v1/webhooks/test")
async def test_webhook(payload: WebhookPayload):
    """Test webhook endpoint for receiving notifications"""
    webhooks_db.append(
        {"received_at": get_current_timestamp(), "payload": payload.dict()}
    )

    return {"message": "Webhook received successfully"}


@case_app.get("/v1/webhooks/history")
async def get_webhook_history(limit: int = Query(default=50, ge=1, le=1000)):
    """Get webhook history for testing"""
    return {"webhooks": webhooks_db[-limit:], "total_count": len(webhooks_db)}


# Health and Monitoring
@case_app.get("/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": get_current_timestamp().isoformat(),
        "stats": {
            "total_cases": len(cases_db),
            "total_documents": len(documents_db),
            "total_jobs": len(jobs_db),
            "active_leases": len(
                [c for c in cases_db.values() if c["lease_expires_at"]]
            ),
        },
    }


@case_app.get("/v1/metrics")
async def get_metrics():
    """Get system metrics"""
    current_time = get_current_timestamp()

    # Calculate metrics
    case_statuses = {}
    job_statuses = {}
    extraction_statuses = {}

    for case in cases_db.values():
        status = case["status"]
        case_statuses[status] = case_statuses.get(status, 0) + 1

        ext_status = case["extraction_status"]
        extraction_statuses[ext_status] = extraction_statuses.get(ext_status, 0) + 1

    for job in jobs_db.values():
        status = job["status"]
        job_statuses[status] = job_statuses.get(status, 0) + 1

    return {
        "timestamp": current_time.isoformat(),
        "case_statuses": case_statuses,
        "job_statuses": job_statuses,
        "extraction_statuses": extraction_statuses,
        "active_leases": len(
            [
                c
                for c in cases_db.values()
                if c["lease_expires_at"] and c["lease_expires_at"] > current_time
            ]
        ),
    }


# Alias for uvicorn compatibility
app = case_app

if __name__ == "__main__":
    uvicorn.run("case_management_api:app", host="0.0.0.0", port=8001, reload=True)
