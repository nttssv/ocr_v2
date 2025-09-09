# OCR PDF Processing API

A high-performance FastAPI-based OCR service for processing PDF documents with Vietnamese text extraction, quality analysis, and organized file output.

## 🚀 Features

- **Multi-language OCR**: Supports Vietnamese, English, and combined language processing
- **Quality Analysis**: Automatic detection of skew, orientation, blank pages, and handwriting
- **Parallel Processing**: Optimized multi-threaded page processing for faster results
- **Organized Output**: Filename-based folders with separate subdirectories for PDFs and text files
- **Performance Optimized**: 85% faster processing with streamlined OCR pipeline
- **RESTful API**: Easy integration with web applications and services

## 📁 Project Structure

```
ocr_v2/
├── api.py                    # Main FastAPI application
├── ocr_client.py             # Command-line client for testing
├── demo_client.py            # Interactive demo script
├── integration_test.py       # Comprehensive integration test suite
├── api_status_check.py       # Quick API status monitoring
├── remote_client.py          # Remote access Python client
├── setup_remote_access.py    # Remote access setup script
├── direct_access.sh          # Quick command-line access script
├── ssh_tunnel.sh             # SSH tunnel management script
├── integration_test_report.md # Detailed test results report
├── REMOTE_ACCESS_GUIDE.md    # Complete remote access guide
├── requirements.txt          # Python dependencies
├── requirements_client.txt   # Client dependencies
├── requirements_remote.txt   # Remote client dependencies
├── README.md                 # This documentation
├── CLIENT_README.md          # Client usage documentation
├── ocr_env/                  # Python virtual environment
├── samples/                  # Sample PDF files for testing
│   ├── 1.pdf                # 4-page Vietnamese legal document
│   ├── 2.pdf                # 9-page Vietnamese court document
│   ├── 3.pdf                # 30-page Vietnamese legal document
│   └── 4.pdf                # 7-page Vietnamese legal document
└── output/                   # Processed results
    ├── 1/                    # Results for 1.pdf
    │   ├── 1_analysis.json
    │   ├── pdf/              # Individual page PDFs
    │   │   ├── 1_page1.pdf
    │   │   └── ...
    │   └── text/             # Extracted text files
    │       ├── 1_page1.txt
    │       └── ...
    ├── 2/                    # Results for 2.pdf
    ├── 3/                    # Results for 3.pdf
    └── 4/                    # Results for 4.pdf
```

## 🖥️ Hardware Requirements

### Recommended System Configuration

**Minimum Requirements:**
- **CPU**: 4+ cores (x86_64 architecture)
- **RAM**: 8 GB
- **Storage**: 20 GB free space (SSD recommended)
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows

**Optimal Performance Configuration:**
- **CPU**: 8+ cores (AMD EPYC or Intel Xeon recommended)
- **RAM**: 32+ GB
- **Storage**: 100+ GB SSD
- **Network**: High-speed internet for API access

### Current Test Environment

**System Specifications:**
- **Platform**: Google Cloud Platform Virtual Machine
- **CPU**: AMD EPYC 7B13 (16 cores, 32 threads)
- **RAM**: 64 GB DDR4
- **Storage**: 200 GB SSD (180 GB available)
- **OS**: Ubuntu 24.04 LTS (Linux 6.14.0-1014-gcp)
- **Network**: 10 Gbps internal network

**Performance Metrics:**
- **Processing Speed**: ~2.2 seconds per page
- **Memory Usage**: 2.6% (1.7 GB used of 64 GB)
- **CPU Usage**: 0.6% (idle: 99.4%)
- **Concurrent Processing**: Up to 16 parallel pages
- **API Response Time**: <100ms for health checks

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

Based on processing the included sample documents on AMD EPYC 7B13 (16 cores, 64 GB RAM):

| Document | Pages | Processing Time | Performance | Quality Issues | Hardware Utilization |
|----------|-------|----------------|-------------|----------------|---------------------|
| 1.pdf    | 4     | 19.88s        | 4.97s/page  | 0 issues       | 2.6% RAM, 0.6% CPU  |
| 2.pdf    | 9     | 34.32s        | 3.81s/page  | 0 issues       | 2.6% RAM, 0.6% CPU  |
| 3.pdf    | 30    | 90.13s        | 3.00s/page  | 1 issue        | 2.6% RAM, 0.6% CPU  |
| 4.pdf    | 7     | 19.93s        | 2.84s/page  | 0 issues       | 2.6% RAM, 0.6% CPU  |

**Hardware Performance Characteristics:**
- **Average Processing Speed**: ~3.2 seconds per page
- **Memory Efficiency**: 2.6% RAM utilization (1.7 GB of 64 GB)
- **CPU Efficiency**: 0.6% CPU utilization (99.4% idle)
- **Parallel Processing**: Up to 16 concurrent pages (2 workers configured)
- **Storage I/O**: Minimal impact on SSD performance
- **API Response Time**: <100ms for health checks

**Scalability Metrics:**
- **Total Documents Processed**: 4 PDFs (50 pages total)
- **Files Generated**: 104 files (50 PDFs + 50 text + 4 analysis)
- **Storage Used**: 6.7 GB (4% of 200 GB available)
- **Processing Success Rate**: 100% (no failures)
- **Quality Detection**: 1 issue detected across 50 pages

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
- `WORKERS`: Number of parallel processing workers (default: 4)

### Performance Tuning

```python
# In api.py, adjust these parameters:
thread_pool = ThreadPoolExecutor(max_workers=4)  # Parallel processing
max_workers=min(4, total_pages)  # Per-document parallelism
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

### Integration Test Suite

The project includes a comprehensive integration test suite that validates all API functionality:

```bash
# Run full integration test
python integration_test.py --file samples/1.pdf --verbose

# Test with different files
python integration_test.py --file samples/2.pdf
python integration_test.py --file samples/3.pdf
python integration_test.py --file samples/4.pdf

# Quick API status check
python api_status_check.py

# Watch mode for monitoring
python api_status_check.py --watch
```

### Test Results

**Integration Test Status**: ✅ 100% PASSED (18/18 tests)

| Test File | Pages | Processing Time | Success Rate | Status |
|-----------|-------|----------------|--------------|--------|
| 1.pdf     | 4     | 20.01s        | 100%        | ✅ PASSED |
| 2.pdf     | 9     | 35.02s        | 100%        | ✅ PASSED |

### Manual Testing

```bash
# Test all sample documents
for i in {1..4}; do
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

## 🌐 Remote Access

### Quick Setup

```bash
# Run the setup script
python setup_remote_access.py

# Test API health
./direct_access.sh health

# Upload a document
./direct_access.sh upload samples/1.pdf
```

### Access Methods

#### 1. Direct Access (if firewall allows)
```bash
# API URL: http://10.148.0.2:8000
python remote_client.py --url http://10.148.0.2:8000 --health
python remote_client.py --url http://10.148.0.2:8000 --file your_document.pdf
```

#### 2. SSH Tunnel (Recommended)
```bash
# Create SSH tunnel
ssh -L 8000:localhost:8000 gcpcoder@YOUR_SERVER_IP

# Use localhost in another terminal
python remote_client.py --url http://localhost:8000 --health
```

#### 3. Quick Commands
```bash
# Health check
./direct_access.sh health

# Upload document
./direct_access.sh upload your_document.pdf

# Check status
./direct_access.sh status DOCUMENT_ID
```

### Python Client Examples

```python
from remote_client import RemoteOCRClient

# Initialize client
client = RemoteOCRClient("http://10.148.0.2:8000")

# Check health
health = client.health_check()
print(f"API Status: {health['status']}")

# Process document
result = client.process_document("your_document.pdf", language="vie")
print(f"Processed {result['total_pages']} pages in {result['processing_time']:.2f}s")
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

### Hardware-Specific Optimizations

**For High-Performance Systems (16+ cores, 32+ GB RAM):**
- Increase `max_workers` to 4-8 for better parallelization
- Enable handwriting detection for better accuracy
- Process multiple documents simultaneously
- Use SSD storage for faster I/O operations

**For Resource-Constrained Systems (4-8 cores, 8-16 GB RAM):**
- Keep `max_workers` at 2 (default)
- Disable handwriting detection for speed
- Process documents sequentially
- Monitor memory usage for large PDFs

**Cloud Deployment Recommendations:**
- **Google Cloud**: Use n2-highmem instances (8+ vCPUs, 64+ GB RAM)
- **AWS**: Use r5.xlarge or larger instances
- **Azure**: Use D-series VMs with 8+ cores and 32+ GB RAM
- **Storage**: Use SSD-backed storage for temporary files

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