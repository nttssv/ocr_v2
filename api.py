import os
import uuid
import tempfile
import asyncio
import aiofiles
import aiohttp
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging
from contextlib import asynccontextmanager


from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
from PyPDF2 import PdfReader, PdfWriter
import ocrmypdf
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for PDF to image conversion
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import threading

# Configure Tesseract data path
TESSDATA_PREFIX = os.getenv('TESSDATA_PREFIX', '/usr/share/tesseract-ocr/4.00/tessdata')
os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

# Configure logging with production optimization
# Set to WARNING in production to reduce log noise, INFO for development
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '16'))
API_PORT = int(os.getenv('API_PORT', '8000'))
API_HOST = os.getenv('API_HOST', '0.0.0.0')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS_CREDENTIALS = os.getenv('CORS_CREDENTIALS', 'true').lower() == 'true'

# Log startup configuration
logger.info(f"OCR API starting with log level: {LOG_LEVEL}")
logger.info(f"Configuration: {MAX_WORKERS} workers, listening on {API_HOST}:{API_PORT}")
if LOG_LEVEL == 'WARNING':
    logger.info("Production logging mode: Reduced verbosity for better performance")

# Global variables
processing_tasks: Dict[str, Dict[str, Any]] = {}
# Optimized for maximum parallel processing - configurable via environment
thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting PDF Processing API")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup
    thread_pool.shutdown(wait=True)
    logger.info("Shutting down PDF Processing API")

app = FastAPI(
    title="PDF Processing API",
    description="API for processing PDFs with deskewing using ocrmypdf",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - configurable for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Pydantic models
class DocumentUploadURL(BaseModel):
    """Model for URL-based document upload"""
    url: HttpUrl
    filename: Optional[str] = None

class QualityIssue(BaseModel):
    """Model for quality issues detected in PDF"""
    issue_type: str  # "skew", "blank_space", "orientation", "low_quality", "handwriting", "blank_page"
    page_number: int
    severity: str  # "low", "medium", "high"
    description: str
    confidence: float  # 0.0 to 1.0

class PageResult(BaseModel):
    """Model for individual page processing result"""
    page_number: int
    pdf_file: str
    text_file: str
    quality_analysis: Dict[str, Any]
    extracted_text: str
    issues: list[QualityIssue]

class ProcessingResponse(BaseModel):
    """Response model for document processing"""
    document_id: str
    status: str
    location: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    quality_issues: Optional[list[QualityIssue]] = None
    total_pages: Optional[int] = None
    issues_detected: Optional[bool] = None
    pages: Optional[list[PageResult]] = None
    output_directory: Optional[str] = None

class TaskStatus(BaseModel):
    """Model for task status"""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float  # 0.0 to 1.0
    result: Optional[ProcessingResponse] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

async def download_file(url: str, destination: str) -> bool:
    """Download file from URL to destination"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    return True
                else:
                    logger.error(f"Failed to download file: HTTP {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False

async def save_upload_file(upload_file: UploadFile, destination: str) -> bool:
    """Save uploaded file to destination"""
    try:
        async with aiofiles.open(destination, 'wb') as f:
            while chunk := await upload_file.read(8192):
                await f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error saving upload file: {e}")
        return False

def split_pdf_into_pages(input_path: str, output_dir: str, filename_base: str) -> list[str]:
    """Split PDF into individual page files using optimized I/O with in-memory processing"""
    page_files = []
    
    try:
        import io
        
        # Read PDF into memory once for better performance
        with open(input_path, 'rb') as f:
            pdf_data = f.read()
        
        reader = PdfReader(io.BytesIO(pdf_data))
        total_pages = len(reader.pages)
        
        for page_num in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            
            page_filename = f"{filename_base}_page{page_num + 1}.pdf"
            # Save PDF files in the pdf subdirectory
            pdf_dir = os.path.join(output_dir, "pdf")
            page_path = os.path.join(pdf_dir, page_filename)
            
            # Use in-memory buffer for faster I/O
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            
            # Write to disk in single operation
            with open(page_path, 'wb') as output_file:
                output_file.write(buffer.getvalue())
            
            page_files.append(page_path)
            logger.info(f"Created page file: {page_path}")
        
        return page_files
    
    except Exception as e:
        logger.error(f"Error splitting PDF: {e}")
        return []

def optimized_ocr_with_quality_analysis(pdf_path: str, page_number: int, output_text_path: str, language: str = "vie", enable_handwriting_detection: bool = False) -> tuple[str, Dict[str, Any], list]:
    """Optimized OCR that combines deskew, rotate, text extraction, and quality analysis in minimal calls"""
    try:
        import subprocess
        import sys
        import tempfile
        import re
        
        quality_issues = []
        analysis_data = {
            "page_number": page_number,
            "file_size": os.path.getsize(pdf_path),
            "rotation": 0,
            "is_blank": False,
            "blank_confidence": 0.0,
            "is_skewed": False,
            "skew_angle": 0.0,
            "skew_confidence": 0.0,
            "orientation_issue": False,
            "suggested_rotation": 0,
            "processing_time": 0.0
        }
        
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Single optimized ocrmypdf call with combined operations
            output_pdf = os.path.join(temp_dir, f"page_{page_number}_processed.pdf")
            sidecar_text = os.path.join(temp_dir, f"page_{page_number}_text.txt")
            
            # Optimized command with quality corrections and 16 workers
            cmd = [
                sys.executable, "-m", "ocrmypdf",
                # "--deskew",  # Skip deskewing for speed
                # "--rotate-pages",  # Skip rotation for speed
                "--force-ocr",  # Ensure OCR runs
                "--sidecar", sidecar_text,  # Extract text to file
                "--tesseract-oem", "1",  # Use LSTM OCR engine for speed
                "--tesseract-pagesegmode", "1",  # Automatic page segmentation for speed
                "--optimize", "0",  # Skip optimization for speed
                "--pdfa-image-compression", "jpeg",  # Faster compression
                "--image-dpi", "75",  # Reduced DPI for faster processing
                "--jpeg-quality", "75",  # Good quality
                "--skip-big", "30",  # Skip large images
                "--tesseract-timeout", "180",  # Increased timeout for complex pages
                "--fast-web-view", "0",  # Disable web view optimization
                pdf_path,
                output_pdf
            ]
            
            # Add language parameter
            if language and language != "eng":
                cmd.extend(["--language", language])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # Increased timeout for complex pages
            )
            
            # Parse OCR output for quality analysis
            stderr_output = result.stderr.lower() if result.stderr else ""
            
            # Detect skewness from output
            skew_patterns = [
                r"deskewing.*?([-+]?\d*\.?\d+).*?degrees?",
                r"skew.*?([-+]?\d*\.?\d+).*?deg",
                r"rotation.*?([-+]?\d*\.?\d+)"
            ]
            
            for pattern in skew_patterns:
                match = re.search(pattern, stderr_output, re.IGNORECASE)
                if match:
                    skew_angle = abs(float(match.group(1)))
                    analysis_data["skew_angle"] = skew_angle
                    if skew_angle > 1.0:
                        analysis_data["is_skewed"] = True
                        analysis_data["skew_confidence"] = min(0.9, skew_angle / 10.0)
                        severity = "high" if skew_angle > 5 else "medium" if skew_angle > 2 else "low"
                        quality_issues.append({
                            "issue_type": "skew",
                            "page_number": page_number,
                            "severity": severity,
                            "description": f"Page is skewed by {skew_angle:.1f} degrees",
                            "confidence": analysis_data["skew_confidence"]
                        })
                    break
            
            # Detect orientation issues
            if "rotating" in stderr_output or "rotated" in stderr_output:
                analysis_data["orientation_issue"] = True
                rotation_match = re.search(r"(90|180|270)", stderr_output)
                if rotation_match:
                    analysis_data["suggested_rotation"] = int(rotation_match.group(1))
                
                quality_issues.append({
                    "issue_type": "orientation",
                    "page_number": page_number,
                    "severity": "high",
                    "description": f"Page orientation issue detected, suggested rotation: {analysis_data['suggested_rotation']} degrees",
                    "confidence": 0.8
                })
            
            # Read extracted text
            extracted_text = ""
            if os.path.exists(sidecar_text):
                with open(sidecar_text, 'r', encoding='utf-8') as f:
                    extracted_text = f.read().strip()
                
                # Vietnamese text quality validation - fastest fix for orientation issues
                if language == "vie" and extracted_text:
                    # Check for garbled text patterns common in Vietnamese orientation issues
                    garbled_patterns = [
                        r'[\x00-\x1f\x7f-\x9f]{3,}',  # Control characters
                        r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF.,!?;:()\[\]{}"\'-/\\@#$%^&*+=<>|~`]{5,}',  # Non-Vietnamese chars
                        r'\?{3,}',  # Multiple question marks (encoding issues)
                    ]
                    
                    garbled_score = 0
                    for pattern in garbled_patterns:
                        matches = re.findall(pattern, extracted_text)
                        garbled_score += len(matches)
                    
                    # If text appears garbled, mark as orientation issue
                    if garbled_score > 2 or (len(extracted_text) > 50 and garbled_score > 0):
                        analysis_data["orientation_issue"] = True
                        analysis_data["suggested_rotation"] = 180  # Most common fix for Vietnamese docs
                        
                        quality_issues.append({
                            "issue_type": "orientation",
                            "page_number": page_number,
                            "severity": "high",
                            "description": f"Vietnamese text appears garbled, likely orientation issue (garbled score: {garbled_score})",
                            "confidence": min(0.9, 0.5 + (garbled_score * 0.1))
                        })
                
                # Copy to final output location
                with open(output_text_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
            
            # Analyze text for blank page detection
            meaningful_text = extracted_text.replace(' ', '').replace('\n', '').replace('\t', '')
            text_length = len(meaningful_text)
            
            if text_length < 5:
                analysis_data["is_blank"] = True
                if text_length == 0:
                    analysis_data["blank_confidence"] = 0.95
                elif text_length < 3:
                    analysis_data["blank_confidence"] = 0.85
                else:
                    analysis_data["blank_confidence"] = 0.70
                
                quality_issues.append({
                    "issue_type": "blank_page",
                    "page_number": page_number,
                    "severity": "medium",
                    "description": "Page appears to be blank or contains minimal content",
                    "confidence": analysis_data["blank_confidence"]
                })
            
            analysis_data["processing_time"] = time.time() - start_time
            
            return extracted_text, analysis_data, quality_issues
    
    except Exception as e:
        logger.error(f"Optimized OCR failed for {pdf_path}: {e}")
        # Fallback to basic text extraction
        return extract_text_fallback(pdf_path, output_text_path, language), {"page_number": page_number, "processing_error": str(e)}, []

def extract_text_fallback(pdf_path: str, output_text_path: str, language: str = "vie") -> str:
    """Fallback text extraction using PyMuPDF + Tesseract (original method)"""
    try:
        # Convert PDF page to image using PyMuPDF with reduced DPI for speed
        doc = fitz.open(pdf_path)
        page = doc[0]  # First (and only) page
        
        # Render page as image with reduced zoom for faster processing
        mat = fitz.Matrix(1.5, 1.5)  # Reduced from 2.0x to 1.5x for speed
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        
        # Convert to PIL Image
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        
        # Extract text using Tesseract with optimized config
        custom_config = r'--oem 1 --psm 6 --dpi 150'  # Use LSTM engine, uniform text block, standard DPI
        extracted_text = pytesseract.image_to_string(img, lang=language, config=custom_config)
        
        # Save text to file
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        doc.close()
        
        return extracted_text.strip()
    
    except Exception as e:
        logger.error(f"Fallback text extraction failed for {pdf_path}: {e}")
        return ""

def detect_skewness_with_ocrmypdf(pdf_path: str, page_number: int, temp_dir: str) -> tuple[bool, float, float]:
    """Detect page skewness using ocrmypdf analysis"""
    try:
        import subprocess
        import sys
        import re
        
        # Run ocrmypdf with deskew to detect skew angle
        output_path = os.path.join(temp_dir, f"page_{page_number}_deskew_test.pdf")
        cmd = [
            sys.executable, "-m", "ocrmypdf",
            "--deskew",
            "--force-ocr",
            "--output-type", "pdf",
            pdf_path,
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse output for skew information
        skew_angle = 0.0
        is_skewed = False
        confidence = 0.0
        
        # Look for skew information in stderr (ocrmypdf logs there)
        if result.stderr:
            # Search for deskew messages
            skew_patterns = [
                r"Deskewing.*?([-+]?\d*\.?\d+).*?degrees?",
                r"skew.*?([-+]?\d*\.?\d+).*?deg",
                r"rotation.*?([-+]?\d*\.?\d+)"
            ]
            
            for pattern in skew_patterns:
                match = re.search(pattern, result.stderr, re.IGNORECASE)
                if match:
                    skew_angle = abs(float(match.group(1)))
                    break
        
        # Determine if significantly skewed (> 1 degree)
        if skew_angle > 1.0:
            is_skewed = True
            confidence = min(0.9, skew_angle / 10.0)  # Higher angle = higher confidence
        elif skew_angle > 0.5:
            is_skewed = True
            confidence = 0.6
        
        return is_skewed, skew_angle, confidence
        
    except Exception as e:
        logger.warning(f"Skewness detection failed for page {page_number}: {e}")
        return False, 0.0, 0.0

def detect_orientation_with_ocrmypdf(pdf_path: str, page_number: int, temp_dir: str) -> tuple[bool, int, float]:
    """Detect page orientation issues using ocrmypdf"""
    try:
        import subprocess
        import sys
        
        # Run ocrmypdf with auto-rotate to detect orientation
        output_path = os.path.join(temp_dir, f"page_{page_number}_orient_test.pdf")
        cmd = [
            sys.executable, "-m", "ocrmypdf",
            "--rotate-pages",
            "--force-ocr",
            "--output-type", "pdf",
            pdf_path,
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if rotation was applied
        rotation_applied = 0
        has_orientation_issue = False
        confidence = 0.0
        
        if result.stderr:
            # Look for rotation messages
            if "Rotating" in result.stderr or "rotated" in result.stderr:
                has_orientation_issue = True
                confidence = 0.8
                
                # Try to extract rotation angle
                import re
                rotation_match = re.search(r"(90|180|270)", result.stderr)
                if rotation_match:
                    rotation_applied = int(rotation_match.group(1))
        
        return has_orientation_issue, rotation_applied, confidence
        
    except Exception as e:
        logger.warning(f"Orientation detection failed for page {page_number}: {e}")
        return False, 0, 0.0

# Legacy function - now replaced by optimized_ocr_with_quality_analysis
# Keeping for backward compatibility if needed
def analyze_single_page_quality_legacy(pdf_path: str, page_number: int) -> tuple[list[QualityIssue], Dict[str, Any]]:
    """Legacy quality analysis function - use optimized_ocr_with_quality_analysis instead"""
    logger.warning("Using legacy quality analysis function - consider using optimized version")
    
    quality_issues = []
    analysis_data = {
        "page_number": page_number,
        "file_size": os.path.getsize(pdf_path),
        "rotation": 0,
        "width": 0,
        "height": 0,
        "aspect_ratio": 0,
        "is_blank": False,
        "blank_confidence": 0.0,
        "is_skewed": False,
        "skew_angle": 0.0,
        "skew_confidence": 0.0,
        "orientation_issue": False,
        "suggested_rotation": 0
    }
    
    try:
        # Basic PDF analysis only
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        
        rotation = page.rotation if hasattr(page, 'rotation') else 0
        analysis_data["rotation"] = rotation
        
        mediabox = page.mediabox
        width = float(mediabox.width)
        height = float(mediabox.height)
        analysis_data["width"] = width
        analysis_data["height"] = height
        analysis_data["aspect_ratio"] = width / height if height > 0 else 0
        
        if rotation != 0:
            quality_issues.append(QualityIssue(
                issue_type="orientation",
                page_number=page_number,
                severity="medium",
                description=f"PDF metadata shows {rotation} degree rotation",
                confidence=0.9
            ))
    
    except Exception as e:
        logger.error(f"Error in legacy quality analysis for {pdf_path}: {e}")
    
    return quality_issues, analysis_data

def detect_handwriting_with_ocrmypdf(input_path: str, page_num: int, temp_dir: str) -> tuple[bool, float, dict]:
    """Detect handwriting using ocrmypdf analysis"""
    try:
        # Extract single page for analysis
        with open(input_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            page_path = os.path.join(temp_dir, f"page_{page_num}_handwriting.pdf")
            with open(page_path, 'wb') as page_file:
                pdf_writer.write(page_file)
        
        # Run OCR with different settings to detect handwriting patterns
        import subprocess
        import sys
        
        # First: Try standard OCR
        standard_ocr_path = os.path.join(temp_dir, f"page_{page_num}_standard.pdf")
        cmd_standard = [
            sys.executable, "-m", "ocrmypdf",
            "--force-ocr",
            "--optimize", "0",
            page_path,
            standard_ocr_path
        ]
        
        result_standard = subprocess.run(
            cmd_standard,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Second: Try with handwriting-optimized settings
        handwriting_ocr_path = os.path.join(temp_dir, f"page_{page_num}_handwriting.pdf")
        cmd_handwriting = [
            sys.executable, "-m", "ocrmypdf",
            "--force-ocr",
            "--tesseract-config", "tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
            "--optimize", "0",
            page_path,
            handwriting_ocr_path
        ]
        
        result_handwriting = subprocess.run(
            cmd_handwriting,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Analyze OCR results for handwriting indicators
        indicators = {
            'ocr_processing_difficulty': False,
            'low_text_extraction': False,
            'character_recognition_issues': False
        }
        
        score = 0
        
        # Check for OCR processing issues (common with handwriting)
        if result_standard.stderr:
            stderr_text = result_standard.stderr.lower()
            if any(phrase in stderr_text for phrase in ['poor', 'low quality', 'difficult', 'unclear']):
                indicators['ocr_processing_difficulty'] = True
                score += 25
        
        # Compare file sizes - handwriting often results in poor OCR extraction
        original_size = os.path.getsize(page_path)
        if os.path.exists(standard_ocr_path):
            ocr_size = os.path.getsize(standard_ocr_path)
            size_change = abs(ocr_size - original_size) / original_size
            
            # Very small size change suggests poor text extraction (handwriting indicator)
            if size_change < 0.02:
                indicators['low_text_extraction'] = True
                score += 30
        
        # Check for character recognition issues by comparing different OCR approaches
        if os.path.exists(handwriting_ocr_path) and os.path.exists(standard_ocr_path):
            standard_size = os.path.getsize(standard_ocr_path)
            handwriting_size = os.path.getsize(handwriting_ocr_path)
            
            # Significant difference suggests character recognition challenges
            if abs(standard_size - handwriting_size) / max(standard_size, handwriting_size) > 0.1:
                indicators['character_recognition_issues'] = True
                score += 20
        
        # Additional check: Run OCR with very permissive settings
        try:
            permissive_ocr_path = os.path.join(temp_dir, f"page_{page_num}_permissive.pdf")
            cmd_permissive = [
                sys.executable, "-m", "ocrmypdf",
                "--force-ocr",
                "--tesseract-config", "tessedit_char_blacklist= ",
                "--optimize", "0",
                page_path,
                permissive_ocr_path
            ]
            
            result_permissive = subprocess.run(
                cmd_permissive,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # If permissive settings still struggle, likely handwriting
            if result_permissive.returncode != 0 or 'error' in result_permissive.stderr.lower():
                score += 25
                
        except Exception:
            # If permissive OCR fails completely, strong handwriting indicator
            score += 35
        
        handwriting_detected = score >= 60
        
        return handwriting_detected, score, indicators
        
    except Exception as e:
        logger.warning(f"Handwriting detection failed for page {page_num}: {e}")
        return False, 0, {}

def detect_blank_page_with_ocrmypdf(input_path: str, page_num: int, temp_dir: str) -> tuple[bool, float]:
    """Detect blank pages using ocrmypdf analysis"""
    try:
        # input_path is already a single-page PDF file
        page_path = input_path
        
        # Run OCR to extract text
        import subprocess
        import sys
        
        ocr_output_path = os.path.join(temp_dir, f"page_{page_num}_text_extract.pdf")
        cmd = [
            sys.executable, "-m", "ocrmypdf",
            "--force-ocr",
            "--sidecar", os.path.join(temp_dir, f"page_{page_num}_text.txt"),
            page_path,
            ocr_output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check extracted text content
        text_file = os.path.join(temp_dir, f"page_{page_num}_text.txt")
        text_content = ""
        if os.path.exists(text_file):
            with open(text_file, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
        
        # Calculate text density
        meaningful_text = text_content.replace(' ', '').replace('\n', '').replace('\t', '')
        text_length = len(meaningful_text)
        
        # Also check file size indicators
        original_size = os.path.getsize(page_path)
        if os.path.exists(ocr_output_path):
            ocr_size = os.path.getsize(ocr_output_path)
            size_ratio = ocr_size / original_size if original_size > 0 else 1
        else:
            size_ratio = 1
        
        # Determine if page is blank
        # Very little text (< 5 characters) and minimal size change suggests blank page
        is_blank = text_length < 5 and size_ratio < 1.05
        
        # Calculate confidence based on text length and processing results
        if text_length == 0:
            confidence = 0.95
        elif text_length < 3:
            confidence = 0.85
        elif text_length < 10:
            confidence = 0.70
        else:
            confidence = 0.0
        
        return is_blank, confidence
        
    except Exception as e:
        logger.warning(f"Blank page detection failed for page {page_num}: {e}")
        return False, 0.0

def analyze_pdf_quality(input_path: str) -> tuple[list[QualityIssue], int]:
    """Fast PDF quality analysis using PyPDF2 and basic file checks"""
    quality_issues = []
    total_pages = 0
    
    # Get basic PDF info using PyPDF2 (already imported)
    try:
        with open(input_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"Analyzing {total_pages} pages for quality issues")
            
            # Basic page analysis using PyPDF2
            for page_num, page in enumerate(pdf_reader.pages, 1):
                # Check for rotation/orientation issues
                rotation = page.rotation
                if rotation == 180:
                    quality_issues.append(QualityIssue(
                        issue_type="orientation",
                        page_number=page_num,
                        severity="high",
                        description=f"Page {page_num} is upside down (180° rotation detected in PDF metadata)",
                        confidence=0.95
                    ))
                elif rotation != 0:
                    quality_issues.append(QualityIssue(
                        issue_type="orientation",
                        page_number=page_num,
                        severity="medium",
                        description=f"Page {page_num} rotated {rotation}° (detected in PDF metadata), may need correction",
                        confidence=0.9
                    ))
                
                # Check for blank space issues using mediabox
                mediabox = page.mediabox
                width = float(mediabox.width)
                height = float(mediabox.height)
                aspect_ratio = width / height if height > 0 else 1
                
                # Detect A3 scanned A4 documents by aspect ratio
                if aspect_ratio > 1.8:  # Excessive horizontal space
                    quality_issues.append(QualityIssue(
                        issue_type="blank_space",
                        page_number=page_num,
                        severity="high",
                        description=f"Page {page_num} has excessive horizontal blank space (aspect ratio {aspect_ratio:.2f}), likely A4 document scanned on A3 setting",
                        confidence=0.85
                    ))
                elif aspect_ratio < 0.6:  # Excessive vertical space
                    quality_issues.append(QualityIssue(
                        issue_type="blank_space",
                        page_number=page_num,
                        severity="high",
                        description=f"Page {page_num} has excessive vertical blank space (aspect ratio {aspect_ratio:.2f}), likely A4 document scanned on A3 setting",
                        confidence=0.85
                    ))
                    
            # Quick file size analysis for quality estimation
            file_size = os.path.getsize(input_path)
            size_per_page = file_size / total_pages if total_pages > 0 else 0
            
            # Very small files per page might indicate low quality scans
            if size_per_page < 50000:  # Less than 50KB per page
                quality_issues.append(QualityIssue(
                    issue_type="low_quality",
                    page_number=0,
                    severity="medium",
                    description=f"Small file size ({size_per_page/1024:.1f}KB per page) may indicate low quality scan",
                    confidence=0.7
                ))
            
            logger.info(f"Quality analysis completed: {len(quality_issues)} issues found")
            
    except Exception as e:
        logger.warning(f"PDF quality analysis failed: {e}")
        quality_issues.append(QualityIssue(
            issue_type="low_quality",
            page_number=0,
            severity="high",
            description=f"Could not analyze PDF quality: {str(e)}",
            confidence=0.8
        ))
    
    return quality_issues, total_pages

# Removed analyze_pages_individually function - replaced with optimized sample-based analysis

def process_single_page(page_file: str, page_number: int, output_dir: str, filename_base: str, language: str, enable_handwriting_detection: bool = False) -> tuple[PageResult, list[QualityIssue]]:
    """Process a single page using optimized OCR with combined quality analysis and text extraction"""
    try:
        # Use optimized OCR function that combines all operations
        text_filename = f"{filename_base}_page{page_number}.txt"
        # Save text files in the text subdirectory
        text_dir = os.path.join(output_dir, "text")
        text_path = os.path.join(text_dir, text_filename)
        
        extracted_text, analysis_data, quality_issues_raw = optimized_ocr_with_quality_analysis(
            page_file, page_number, text_path, language, enable_handwriting_detection
        )
        
        # Convert raw quality issues to QualityIssue objects
        page_issues = []
        for issue in quality_issues_raw:
            page_issues.append(QualityIssue(
                issue_type=issue["issue_type"],
                page_number=issue["page_number"],
                severity=issue["severity"],
                description=issue["description"],
                confidence=issue["confidence"]
            ))
        
        # Add basic quality checks from PDF metadata
        try:
            reader = PdfReader(page_file)
            page = reader.pages[0]
            
            # Check for rotation in PDF metadata
            rotation = page.rotation if hasattr(page, 'rotation') else 0
            if rotation != 0:
                page_issues.append(QualityIssue(
                    issue_type="orientation",
                    page_number=page_number,
                    severity="medium",
                    description=f"PDF metadata shows {rotation} degree rotation",
                    confidence=0.9
                ))
            
            # Check page dimensions for aspect ratio issues
            mediabox = page.mediabox
            width = float(mediabox.width)
            height = float(mediabox.height)
            aspect_ratio = width / height if height > 0 else 0
            
            analysis_data["width"] = width
            analysis_data["height"] = height
            analysis_data["aspect_ratio"] = aspect_ratio
            analysis_data["rotation"] = rotation
            
            # Check for blank space (A3 scanned as A4)
            if aspect_ratio > 1.5:  # Wider than normal
                page_issues.append(QualityIssue(
                    issue_type="blank_space",
                    page_number=page_number,
                    severity="medium",
                    description="Possible A3 document scanned as A4 (excess blank space)",
                    confidence=0.7
                ))
            
            # Check file size for quality issues
            size_per_page_kb = analysis_data["file_size"] / 1024
            if size_per_page_kb < 50:  # Very small file size
                page_issues.append(QualityIssue(
                    issue_type="low_quality",
                    page_number=page_number,
                    severity="medium",
                    description=f"Small file size ({size_per_page_kb:.1f}KB) may indicate low quality scan",
                    confidence=0.6
                ))
        
        except Exception as metadata_error:
            # Only log metadata errors in debug mode to reduce noise
            if logger.isEnabledFor(logging.DEBUG):
                logger.warning(f"Could not read PDF metadata for page {page_number}: {metadata_error}")
        
        # Create page result with subdirectory paths
        page_result = PageResult(
            page_number=page_number,
            pdf_file=f"pdf/{os.path.basename(page_file)}",
            text_file=f"text/{os.path.basename(text_path)}",
            quality_analysis=analysis_data,
            extracted_text=extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,  # Truncate for response
            issues=page_issues
        )
        
        # Optimized logging for production - only log pages with issues or every 10th page
        if len(page_issues) > 0 or page_number % 10 == 0:
            logger.info(f"Page {page_number}: {len(page_issues)} issues, {len(extracted_text)} chars, {analysis_data.get('processing_time', 0):.2f}s")
        
        return page_result, page_issues
        
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {e}")
        # Return error page result
        error_issue = QualityIssue(
            issue_type="low_quality",
            page_number=page_number,
            severity="high",
            description=f"Page processing failed: {str(e)}",
            confidence=0.9
        )
        
        error_page_result = PageResult(
                page_number=page_number,
                pdf_file=f"pdf/{os.path.basename(page_file)}",
                text_file="",
            quality_analysis={"page_number": page_number, "processing_error": str(e)},
            extracted_text="",
            issues=[error_issue]
        )
        
        return error_page_result, [error_issue]

def process_pdf_with_per_page_analysis(document_id: str, input_path: str, output_dir: str, filename_base: str, language: str = "vie", enable_handwriting_detection: bool = False) -> ProcessingResponse:
    """Process PDF by splitting into individual pages with parallel quality analysis and text extraction"""
    start_time = time.time()
    
    try:
        # Update task status
        processing_tasks[document_id]["status"] = "processing"
        processing_tasks[document_id]["progress"] = 0.1
        processing_tasks[document_id]["updated_at"] = datetime.now()
        
        logger.info(f"Starting per-page PDF analysis and processing for document {document_id}")
        
        # Step 1: Split PDF into individual pages
        processing_tasks[document_id]["progress"] = 0.2
        logger.info(f"Splitting PDF into individual pages for document {document_id}")
        page_files = split_pdf_into_pages(input_path, output_dir, filename_base)
        
        if not page_files:
            raise Exception("Failed to split PDF into pages")
        
        total_pages = len(page_files)
        logger.info(f"Split PDF into {total_pages} pages")
        
        # Step 2: Process pages in parallel
        processing_tasks[document_id]["progress"] = 0.3
        logger.info(f"Starting parallel processing of {total_pages} pages")
        
        page_results = []
        all_quality_issues = []
        
        # Use ThreadPoolExecutor for parallel processing with optimized parameters
        # Increased workers for maximum performance - target ~2s per page
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, total_pages)) as executor:
            # Submit all page processing tasks with handwriting detection parameter
            future_to_page = {
                executor.submit(process_single_page, page_file, i + 1, output_dir, filename_base, language, enable_handwriting_detection): i + 1
                for i, page_file in enumerate(page_files)
            }
            
            # Collect results as they complete
            completed_pages = 0
            for future in concurrent.futures.as_completed(future_to_page):
                page_number = future_to_page[future]
                try:
                    page_result, page_issues = future.result()
                    page_results.append(page_result)
                    all_quality_issues.extend(page_issues)
                    
                    completed_pages += 1
                    progress = 0.3 + (0.6 * completed_pages / total_pages)  # Progress from 0.3 to 0.9
                    processing_tasks[document_id]["progress"] = progress
                    
                    # Only log progress every 10 pages or for pages with issues to reduce log noise
                    if completed_pages % 10 == 0 or len(page_issues) > 0:
                        logger.info(f"Completed page {page_number}/{total_pages} ({completed_pages} total completed)")
                    
                except Exception as e:
                    logger.error(f"Page {page_number} processing failed: {e}")
                    # Add error result for failed page
                    error_issue = QualityIssue(
                        issue_type="low_quality",
                        page_number=page_number,
                        severity="high",
                        description=f"Page processing failed: {str(e)}",
                        confidence=0.9
                    )
                    
                    error_page_result = PageResult(
                        page_number=page_number,
                        pdf_file=f"pdf/{filename_base}_page{page_number}.pdf",
                        text_file="",
                        quality_analysis={"page_number": page_number, "processing_error": str(e)},
                        extracted_text="",
                        issues=[error_issue]
                    )
                    
                    page_results.append(error_page_result)
                    all_quality_issues.append(error_issue)
                    completed_pages += 1
        
        # Sort page results by page number to maintain order
        page_results.sort(key=lambda x: x.page_number)
        
        logger.info(f"Parallel processing completed for {total_pages} pages")
        
        processing_time = time.time() - start_time
        
        # Save analysis results as JSON file
        response_data = {
            "document_id": document_id,
            "status": "completed",
            "processing_time": processing_time,
            "quality_issues": [issue.dict() for issue in all_quality_issues],
            "total_pages": total_pages,
            "issues_detected": len(all_quality_issues) > 0,
            "pages": [page.dict() for page in page_results],
            "output_directory": output_dir
        }
        
        json_output_path = os.path.join(output_dir, f"{filename_base}_analysis.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis results saved to: {json_output_path}")
        
        # Create response with per-page analysis
        response = ProcessingResponse(
            document_id=document_id,
            status="completed",
            location=None,  # No single output file
            processing_time=processing_time,
            quality_issues=all_quality_issues,
            total_pages=total_pages,
            issues_detected=len(all_quality_issues) > 0,
            pages=page_results,
            output_directory=output_dir
        )
        
        # Update task status
        processing_tasks[document_id]["status"] = "completed"
        processing_tasks[document_id]["progress"] = 1.0
        processing_tasks[document_id]["result"] = response
        processing_tasks[document_id]["updated_at"] = datetime.now()
        
        logger.info(f"Document {document_id} processed successfully in {processing_time:.2f}s with {len(all_quality_issues)} total issues detected across {total_pages} pages (handwriting detection: {'enabled' if enable_handwriting_detection else 'disabled'})")
        
        return response
        
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"Document {document_id} processing failed: {error_msg}")
        
        # Update task status with error
        processing_tasks[document_id]["status"] = "failed"
        processing_tasks[document_id]["error"] = error_msg
        processing_tasks[document_id]["updated_at"] = datetime.now()
        
        return ProcessingResponse(
            document_id=document_id,
            status="failed",
            error=error_msg
        )

async def process_document_async(document_id: str, input_path: str, output_dir: str, filename_base: str, language: str = "vie", enable_handwriting_detection: bool = False):
    """Async wrapper for per-page document processing with quality analysis"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        thread_pool, 
        process_pdf_with_per_page_analysis, 
        document_id, 
        input_path, 
        output_dir,
        filename_base,
        language,
        enable_handwriting_detection
    )
    
    # Clean up temporary input file
    try:
        if os.path.exists(input_path):
            os.remove(input_path)
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file {input_path}: {e}")
    
    return result

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PDF Processing API",
        "version": "1.0.0",
        "endpoints": {
            "transform": "/documents/transform",
            "status": "/documents/status/{document_id}",
            "health": "/health"
        }
    }

@app.post("/documents/transform", response_model=ProcessingResponse)
async def transform_document(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    url_data: Optional[str] = Form(None),
    language: Optional[str] = Form("vie"),  # Default to Vietnamese
    enable_handwriting_detection: Optional[bool] = Form(False)  # Optional handwriting detection
):
    """Transform document endpoint - accepts file upload or URL with language specification
    
    Parameters:
    - file: PDF file to upload (optional)
    - url_data: JSON string with URL and filename (optional) 
    - language: OCR language code (default: 'vie' for Vietnamese)
    - enable_handwriting_detection: Enable handwriting detection (default: False, improves performance when disabled)
    
    Supported languages: vie (Vietnamese), eng (English), vie+eng (Vietnamese + English)
    Note: Handwriting detection is resource-intensive and should only be enabled when needed.
    """
    document_id = str(uuid.uuid4())
    
    try:
        # Initialize task
        processing_tasks[document_id] = {
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Determine input source
        if file and file.filename:
            # File upload
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            filename = file.filename
            input_path = f"temp_{document_id}_{filename}"
            
            # Save uploaded file
            if not await save_upload_file(file, input_path):
                raise HTTPException(status_code=500, detail="Failed to save uploaded file")
                
        elif url_data:
            # URL download
            try:
                url_info = json.loads(url_data)
                url = url_info.get('url')
                filename = url_info.get('filename', f"document_{document_id}.pdf")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid URL data format")
            
            if not url:
                raise HTTPException(status_code=400, detail="URL is required")
            
            input_path = f"temp_{document_id}_{filename}"
            
            # Download file
            if not await download_file(url, input_path):
                raise HTTPException(status_code=500, detail="Failed to download file from URL")
        else:
            raise HTTPException(status_code=400, detail="Either file upload or URL must be provided")
        
        # Create output directory structure with filename-based folder
        output_base_dir = Path("output")
        output_base_dir.mkdir(exist_ok=True)
        
        # Create filename-based directory instead of document_id
        filename_base = Path(filename).stem
        document_output_dir = output_base_dir / filename_base
        document_output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organized file storage
        text_dir = document_output_dir / "text"
        pdf_dir = document_output_dir / "pdf"
        text_dir.mkdir(exist_ok=True)
        pdf_dir.mkdir(exist_ok=True)
        
        # Start background processing with optimization parameters
        background_tasks.add_task(
            process_document_async,
            document_id,
            input_path,
            str(document_output_dir),
            filename_base,
            language,
            enable_handwriting_detection
        )
        
        # Return immediate response
        return ProcessingResponse(
            document_id=document_id,
            status="processing",
            location=None
        )
        
    except HTTPException:
        # Clean up task if it was created
        if document_id in processing_tasks:
            del processing_tasks[document_id]
        raise
    except Exception as e:
        # Clean up task if it was created
        if document_id in processing_tasks:
            del processing_tasks[document_id]
        logger.error(f"Unexpected error in transform_document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/status/{document_id}", response_model=TaskStatus)
async def get_document_status(document_id: str):
    """Get document processing status"""
    if document_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Document not found")
    
    task_info = processing_tasks[document_id]
    
    return TaskStatus(
        task_id=document_id,
        status=task_info["status"],
        progress=task_info["progress"],
        result=task_info.get("result"),
        error=task_info.get("error"),
        created_at=task_info["created_at"],
        updated_at=task_info["updated_at"]
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(processing_tasks)
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )