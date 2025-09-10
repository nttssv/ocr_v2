#!/bin/bash
# Direct Access Script for OCR API
# Usage: ./direct_access.sh [command] [file]

API_URL="http://10.148.0.2:8000"

case "$1" in
    "health")
        curl -s "$API_URL/health" | jq .
        ;;
    "info")
        curl -s "$API_URL/" | jq .
        ;;
    "upload")
        if [ -z "$2" ]; then
            echo "Usage: $0 upload <file.pdf>"
            exit 1
        fi
        curl -X POST "$API_URL/documents/transform"             -F "file=@$2"             -F "language=vie"             -F "enable_handwriting_detection=false"
        ;;
    "status")
        if [ -z "$2" ]; then
            echo "Usage: $0 status <document_id>"
            exit 1
        fi
        curl -s "$API_URL/documents/status/$2" | jq .
        ;;
    *)
        echo "Available commands:"
        echo "  health  - Check API health"
        echo "  info    - Get API information"
        echo "  upload  - Upload a document"
        echo "  status  - Check document status"
        ;;
esac
