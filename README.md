# OCR API with Case Management System

A comprehensive OCR (Optical Character Recognition) API with advanced case management and extraction workflow capabilities, built with FastAPI for high-performance document processing.

## 🚀 Features

### Core OCR Capabilities
- **Multi-language OCR support** with configurable language settings
- **PDF processing** with automatic page splitting and parallel processing
- **Quality analysis** including rotation detection, text extraction confidence, and issue identification
- **Handwriting detection** (optional) for mixed content documents
- **Asynchronous processing** for handling multiple documents efficiently

### Case Management System
- **Case-based document organization** for structured workflow management
- **Job coordination system** with priority-based processing
- **Extraction workflow** with lease-based task distribution
- **Webhook notifications** for real-time status updates
- **Bulk operations** for efficient batch processing
- **Comprehensive monitoring** with metrics and health checks

### API Features
- **RESTful API** with comprehensive error handling and validation
- **Idempotency support** to prevent duplicate operations
- **Cursor-based pagination** for scalable data retrieval
- **Interactive documentation** with Swagger UI
- **Health monitoring** with detailed system status

## 🏗️ Architecture

The system consists of two main components:

1. **OCR API** (`api.py`) - Core document processing on port 8000
2. **Case Management API** (`case_management_api.py`) - Workflow orchestration on port 8001

```
┌─────────────────┐    ┌──────────────────────┐
│   OCR API       │    │  Case Management API │
│   Port 8000     │◄───┤  Port 8001           │
│                 │    │                      │
│ • PDF Processing│    │ • Case Management    │
│ • Text Extraction│   │ • Job Coordination   │
│ • Quality Analysis│  │ • Extraction Workflow│
└─────────────────┘    │ • Webhook System     │
                       └──────────────────────┘
```

## 📁 Project Structure

```
ocr_test/
├── api.py                    # Main OCR FastAPI application
├── case_management_api.py    # Case management system API
├── requirements.txt          # Python dependencies
├── requirements_client.txt   # Client tool dependencies
├── README.md                 # Main documentation
├── API_DOCUMENTATION.md      # API endpoint documentation
├── CLIENT_README.md          # Client tools documentation
├── ocr_client.py            # Command-line OCR client
├── demo_client.py           # Interactive demo client
├── final_test.py            # Comprehensive test suite
├── integration_test.py      # Integration testing
├── create_sample_pdfs.py    # Sample PDF generator
├── samples/                 # Sample PDF files for testing
│   ├── 1.pdf               # 4-page Vietnamese legal document
│   ├── 2.pdf               # 9-page Vietnamese court document
│   ├── 3.pdf               # 30-page Vietnamese legal document
│   └── 4.pdf               # 30-page Vietnamese court judgment
└── output/                  # Processed results
    ├── 1/                   # Results for 1.pdf
    │   ├── 1_analysis.json  # Quality analysis and metadata
    │   ├── pdf/             # Individual page PDFs
    │   │   ├── 1_page1.pdf
    │   │   └── ...
    │   └── text/            # Extracted text files
    │       ├── 1_page1.txt
    │       └── ...
    ├── 2/                   # Results for 2.pdf
    ├── 3/                   # Results for 3.pdf (30 pages)
    └── 4/                   # Results for 4.pdf (30 pages)
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR
- ocrmypdf
- System dependencies for PDF processing

### macOS Installation

```bash
# Install Tesseract and dependencies
brew install tesseract
brew install tesseract-lang  # For additional languages
brew install ghostscript
brew install poppler

# Clone the repository
git clone <repository-url>
cd ocr_test

# Install Python dependencies
pip install -r requirements.txt
```

### Ubuntu/Debian Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng
sudo apt-get install ghostscript poppler-utils

# Install Python dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Start the API Server

```bash
python api.py
```

The server will start on `http://localhost:8000`

### 2. Process a PDF Document

```bash
# Upload a file
curl -X POST "http://localhost:8000/documents/transform" \
  -F "file=@samples/1.pdf" \
  -F "language=vie" \
  -F "enable_handwriting_detection=false"

# Or use a URL
curl -X POST "http://localhost:8000/documents/transform" \
  -F 'url_data={"url":"https://example.com/document.pdf","filename":"document.pdf"}' \
  -F "language=vie"
```

### 3. Check API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📊 Performance Benchmarks

Based on processing the included sample documents (latest test results):

| Document | Pages | Processing Time | Performance | Quality Issues |
|----------|-------|----------------|-------------|----------------|
| 1.pdf    | 4     | 11.05s        | 2.76s/page  | 0 issues       |
| 2.pdf    | 9     | 17.41s        | 1.93s/page  | 0 issues       |
| 3.pdf    | 30    | 35.08s        | 1.17s/page  | 1 quality issue|
| 4.pdf    | 30    | 36.22s        | 1.21s/page  | 0 issues       |

**Key Performance Metrics:**
- **Average Processing Speed**: ~1.2 seconds per page
- **Total Documents Processed**: 73 pages across 4 documents
- **Success Rate**: 100% (4/4 files processed successfully)
- **Parallel Processing**: Up to 16 concurrent workers
- **Memory Efficiency**: In-memory PDF processing with large file support
- **Apple M4 Performance**: Optimized for high-throughput document processing

## 💻 Hardware Configuration & Performance

### Recommended Hardware Configurations

#### High-Performance Setup (Tested)
- **CPU**: Apple M4 chip (10 cores: 4 performance + 6 efficiency)
- **Memory**: 16 GB RAM
- **Storage**: Apple SSD
- **OS**: macOS 15.5
- **Recommended Workers**: 16
- **Expected Performance**: ~1.9 seconds per page

#### Cloud/Server Setup
- **CPU**: AMD EPYC 7B13 (2 cores, 4 threads)
- **Memory**: 15 GB RAM (12 GB available)
- **Storage**: 48 GB root + 196 GB additional disk
- **OS**: Ubuntu 24.04 LTS
- **Recommended Workers**: 4
- **Expected Performance**: ~6-8 seconds per page (3-4x slower)

#### Minimum Requirements
- **CPU**: 2+ cores
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 10 GB free space
- **Recommended Workers**: 2-4

### Performance Comparison

| Hardware | Workers | Per Page | 10 Pages | 50 Pages | Cost |
|----------|---------|----------|----------|----------|---------|
| Apple M4 | 16 | ~2s | ~15s | ~1.5min | High |
| AMD EPYC | 4 | ~7s | ~45s | ~4min | Low |
| Minimum | 2 | ~12s | ~90s | ~8min | Very Low |

### Configuration Guidelines

#### Environment Variables
Copy `.env.example` to `.env` and adjust based on your hardware:

```bash
# For Apple M4 (high-performance)
MAX_WORKERS=16
API_PORT=8000
LOG_LEVEL=INFO

# For AMD EPYC (cloud/server)
MAX_WORKERS=4
API_PORT=8000
LOG_LEVEL=WARNING  # Reduce logging overhead

# For minimum setup
MAX_WORKERS=2
API_PORT=8000
LOG_LEVEL=ERROR
```

#### Memory Considerations
- **Per Worker**: ~2-3 GB RAM usage
- **Apple M4**: 16 workers × 2GB = ~32GB peak (with 16GB physical)
- **AMD EPYC**: 4 workers × 2GB = ~8GB peak (safe for 12GB available)
- **Large PDFs**: May require reducing workers to prevent memory pressure

### Software Environment (Tested)
- **Python**: 3.13.5 (3.8+ supported)
- **Tesseract**: 5.5.1
- **OCR Languages**: Vietnamese (vie), English (eng), and 100+ other languages supported

## 🔧 API Endpoints

### POST `/documents/transform`

Process a PDF document with OCR and quality analysis.

**Parameters:**
- `file` (optional): PDF file upload
- `url_data` (optional): JSON string with URL and filename
- `language` (default: "vie"): OCR language code
- `enable_handwriting_detection` (default: false): Enable handwriting detection

**Supported Languages:**
- `vie`: Vietnamese
- `eng`: English
- `vie+eng`: Vietnamese + English

**Response:**
```json
{
  "document_id": "uuid",
  "status": "completed",
  "processing_time": 9.51,
  "total_pages": 4,
  "issues_detected": false,
  "quality_issues": [],
  "pages": [
    {
      "page_number": 1,
      "pdf_file": "pdf/1_page1.pdf",
      "text_file": "text/1_page1.txt",
      "quality_analysis": {...},
      "extracted_text": "...",
      "issues": []
    }
  ],
  "output_directory": "output/1"
}
```

### GET `/`

Health check endpoint.

## 🎯 Quality Analysis Features

The API automatically detects and reports:

1. **Skew Detection**: Identifies rotated or tilted pages
2. **Orientation Issues**: Detects incorrect page orientation
3. **Blank Pages**: Identifies pages with minimal content
4. **Handwriting Detection**: Optional detection of handwritten content
5. **Low Quality**: Identifies poor scan quality or resolution issues
6. **Blank Space**: Detects A3 documents scanned as A4

## 🔧 Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (INFO, WARNING, DEBUG)
- `WORKERS`: Number of parallel processing workers (default: 16)
- `TESSDATA_PREFIX`: Tesseract data directory (auto-configured)

### Performance Tuning

```python
# In api.py, adjust these parameters:
thread_pool = ThreadPoolExecutor(max_workers=16)  # Parallel processing
max_workers=min(16, total_pages)  # Per-document parallelism
```

### Client Tools

The project includes Python client tools for easy testing:

```bash
# Install client dependencies
pip install -r requirements_client.txt

# Process a document with the client
python ocr_client.py samples/4.pdf -l vie

# Demo client for interactive testing
python demo_client.py
```

## 📝 Output Structure

Each processed document creates:

```
output/[filename]/
├── [filename]_analysis.json    # Complete analysis results
├── pdf/                        # Individual page PDFs
│   ├── [filename]_page1.pdf
│   ├── [filename]_page2.pdf
│   └── ...
└── text/                       # Extracted text files
    ├── [filename]_page1.txt
    ├── [filename]_page2.txt
    └── ...
```

## 🧪 Testing

### Run Sample Tests

```bash
# Test all sample documents
for i in {1..3}; do
  echo "Processing samples/${i}.pdf..."
  curl -X POST "http://localhost:8000/documents/transform" \
    -F "file=@samples/${i}.pdf" \
    -F "language=vie" \
    -F "enable_handwriting_detection=false"
  echo "\n"
done
```

### Verify Results

```bash
# Check output structure
ls -la output/

# View extracted text
head output/1/text/1_page1.txt

# Check analysis results
jq '.processing_time, .total_pages, .issues_detected' output/1/1_analysis.json
```

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng \
    ghostscript poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "api.py"]
```

### Production Settings

```bash
# Set production logging
export LOG_LEVEL=WARNING

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8000
```

## 🔍 Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu
   sudo apt-get install tesseract-ocr
   ```

2. **Vietnamese language not supported**
   ```bash
   # macOS
   brew install tesseract-lang
   
   # Ubuntu
   sudo apt-get install tesseract-ocr-vie
   ```

3. **Memory issues with large PDFs**
   - Reduce `max_workers` in ThreadPoolExecutor
   - Process documents sequentially for very large files

4. **Slow processing**
   - Disable handwriting detection: `enable_handwriting_detection=false`
   - Increase `max_workers` for more parallelism
   - Use SSD storage for temporary files

## 📈 Performance Optimizations

This API includes several performance optimizations:

1. **Combined OCR Operations**: Single ocrmypdf call for deskew, rotate, and text extraction
2. **Parallel Processing**: Multi-threaded page processing
3. **In-Memory Streams**: Reduced file I/O operations
4. **Optimized Tesseract**: Configured for speed with `--oem 1`
5. **Optional Features**: Handwriting detection disabled by default
6. **Reduced Logging**: Production-optimized logging levels

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition
- [ocrmypdf](https://github.com/ocrmypdf/OCRmyPDF) for PDF processing
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [PyPDF2](https://github.com/py-pdf/PyPDF2) for PDF manipulation

## 📞 Support

For issues and questions:
1. Check the [troubleshooting section](#-troubleshooting)
2. Search existing [GitHub issues](../../issues)
3. Create a new issue with detailed information

---

**Built with ❤️ for Vietnamese document processing**