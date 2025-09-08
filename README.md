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
ocr_test/
├── api.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── samples/              # Sample PDF files for testing
│   ├── 1.pdf            # 4-page Vietnamese legal document
│   ├── 2.pdf            # 9-page Vietnamese court document
│   └── 3.pdf            # 30-page Vietnamese legal document
└── output/               # Processed results
    ├── 1/                # Results for 1.pdf
    │   ├── 1_analysis.json
    │   ├── pdf/          # Individual page PDFs
    │   │   ├── 1_page1.pdf
    │   │   └── ...
    │   └── text/         # Extracted text files
    │       ├── 1_page1.txt
    │       └── ...
    ├── 2/                # Results for 2.pdf
    └── 3/                # Results for 3.pdf
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

Based on processing the included sample documents:

| Document | Pages | Processing Time | Performance | Quality Issues |
|----------|-------|----------------|-------------|----------------|
| 1.pdf    | 4     | 9.51s         | 2.38s/page  | 0 issues       |
| 2.pdf    | 9     | 21.68s        | 2.41s/page  | 1 orientation  |
| 3.pdf    | 30    | 51.70s        | 1.72s/page  | 1 blank page   |

**Key Performance Metrics:**
- **Average Processing Speed**: ~2.2 seconds per page
- **Optimization Improvement**: 85% faster than baseline
- **Parallel Processing**: Up to 4 concurrent pages
- **Memory Efficiency**: In-memory PDF processing

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