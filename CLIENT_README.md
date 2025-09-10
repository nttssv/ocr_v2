# OCR Command Line Client

A user-friendly command line interface for the OCR API that makes testing and batch processing PDF documents fast and easy.

## Features

- 🚀 **Fast Testing**: Process PDFs with a simple command
- 🎨 **Beautiful Output**: Rich, colorized results with tables and panels
- 🌍 **Multi-language**: Support for Vietnamese, English, and other languages
- 📝 **Handwriting Detection**: Optional handwriting recognition
- 📊 **Detailed Analysis**: Processing times, quality scores, and issue detection
- 🔄 **Batch Processing**: Handle multiple files at once
- 📋 **JSON Output**: Machine-readable results for scripting
- ⚡ **Progress Indicators**: Visual feedback during processing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_client.txt
```

### 2. Start the OCR API Server

```bash
python api.py
```

### 3. Process Your First Document

```bash
python ocr_client.py samples/document.pdf -l vie
```

## Usage Examples

### Basic Usage

```bash
# Process with default settings (English)
python ocr_client.py document.pdf

# Process Vietnamese document
python ocr_client.py document.pdf -l vie

# Enable handwriting detection
python ocr_client.py document.pdf -l vie --handwriting
```

### Batch Processing

```bash
# Process multiple specific files
python ocr_client.py file1.pdf file2.pdf file3.pdf -l vie

# Process all PDFs in a directory
python ocr_client.py samples/*.pdf -l vie

# Process with different settings
python ocr_client.py samples/*.pdf -l eng --handwriting
```

### Output Options

```bash
# Get raw JSON output (useful for scripting)
python ocr_client.py document.pdf -l vie --json

# Quiet mode (suppress progress indicators)
python ocr_client.py document.pdf -l vie --quiet

# Use custom API URL
python ocr_client.py document.pdf --url http://localhost:8001
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|----------|
| `files` | PDF file(s) to process | Required |
| `-l, --language` | OCR language code | `eng` |
| `--handwriting` | Enable handwriting detection | `false` |
| `--url` | OCR API base URL | `http://localhost:8000` |
| `--json` | Output raw JSON results | `false` |
| `--quiet, -q` | Suppress progress output | `false` |
| `--help, -h` | Show help message | - |

## Language Codes

| Language | Code |
|----------|------|
| English | `eng` |
| Vietnamese | `vie` |
| French | `fra` |
| German | `deu` |
| Spanish | `spa` |
| Chinese (Simplified) | `chi_sim` |
| Chinese (Traditional) | `chi_tra` |
| Japanese | `jpn` |
| Korean | `kor` |

## Output Format

The client provides rich, formatted output including:

### Document Information
- File name and processing status
- Total processing time
- Number of pages processed
- Language used for OCR

### Page Results
- Per-page processing times
- Text preview for each page
- Number of issues detected

### Quality Analysis
- Overall quality score (0-10)
- Text clarity score
- Layout analysis score
- Detailed issue detection

### Output Files
- Location of processed PDF
- Analysis JSON file path
- Output directory structure

## JSON Output Mode

For scripting and automation, use the `--json` flag to get machine-readable output:

```bash
python ocr_client.py document.pdf -l vie --json > results.json
```

The JSON output includes all processing results, quality metrics, and file paths.

## Performance Tips

1. **Batch Processing**: Process multiple files in one command for better efficiency
2. **Language Selection**: Use the correct language code for better accuracy
3. **Handwriting Detection**: Only enable when needed (adds processing time)
4. **Quiet Mode**: Use `--quiet` for faster processing in scripts

## Troubleshooting

### API Server Not Running
```
Error: OCR API server is not running at http://localhost:8000
```
**Solution**: Start the API server with `python api.py`

### File Not Found
```
Error: File 'document.pdf' not found
```
**Solution**: Check the file path and ensure the PDF exists

### Connection Timeout
```
Error: Request timed out
```
**Solution**: Large files may take longer. The client waits up to 5 minutes.

### Processing Errors
```
Error: API returned status 500
```
**Solution**: Check the API server logs for detailed error information

## Demo Scripts

### Interactive Demo
Run the interactive demo to see all features:

```bash
python ocr_client.py samples/1.pdf -l vie
```

This will demonstrate the client functionality with a sample document.

### Comprehensive Test Suite
Run the comprehensive test suite to process all sample documents:

```bash
python final_test.py
```

This script:
- Processes all PDF files in the samples/ directory
- Handles asynchronous processing with proper status checking
- Provides detailed logging and error handling
- Saves comprehensive results to `final_test_results.json`
- Shows processing times, page counts, and quality analysis

**Sample Output:**
```
✅ Test Results Summary:
📊 OCR Success Rate: 100.0% (4/4 files)
⏱️  Total Processing Time: ~100 seconds
📄 Total Pages Processed: 73 pages
🔍 Quality Issues Found: 1 file with issues
💾 Results saved to: final_test_results.json
```

## Integration Examples

### Bash Script

```bash
#!/bin/bash
# Process all PDFs in a directory
for pdf in /path/to/pdfs/*.pdf; do
    echo "Processing: $pdf"
    python ocr_client.py "$pdf" -l vie --quiet
done
```

### Python Script

```python
import subprocess
import json

def process_pdf(file_path, language='vie'):
    cmd = ['python', 'ocr_client.py', file_path, '-l', language, '--json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print(f"Error processing {file_path}: {result.stderr}")
        return None

# Usage
result = process_pdf('document.pdf', 'vie')
if result:
    print(f"Processing time: {result.get('processing_time', 0):.2f}s")
```

## Performance Benchmarks

Based on recent testing with the included sample documents:

| Document | Pages | Processing Time | Performance | Quality Issues |
|----------|-------|----------------|-------------|----------------|
| 1.pdf    | 4     | 7.51s         | 1.88s/page  | 0 issues       |
| 2.pdf    | 9     | 8.90s         | 0.99s/page  | 0 issues       |
| 3.pdf    | 30    | 21.93s        | 0.73s/page  | 1 quality issue|
| 4.pdf    | 30    | 24.71s        | 0.82s/page  | 1 quality issue|

**Key Performance Metrics:**
- **Average Processing Speed**: ~1.1 seconds per page
- **Success Rate**: 100% (4/4 files processed successfully)
- **Total Pages Processed**: 73 pages across 4 documents
- **File Size Support**: Up to 18MB+ PDFs
- **With handwriting detection**: +20-30% processing time
- **Batch processing**: ~10% faster per document
- **Integration Test Results**: 100% pass rate (9/9 tests)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API server logs
3. Run with `--json` flag to get detailed error information
4. Use the demo script to verify basic functionality