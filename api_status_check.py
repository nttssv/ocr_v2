#!/usr/bin/env python3
"""
Quick API Status Check Script

This script provides a quick overview of the OCR API status and performance.
"""

import requests
import json
import time
from datetime import datetime

def check_api_status(base_url="http://localhost:8000"):
    """Check API status and return summary"""
    try:
        # Health check
        health_response = requests.get(f"{base_url}/health", timeout=5)
        health_data = health_response.json() if health_response.status_code == 200 else None
        
        # API info
        info_response = requests.get(f"{base_url}/", timeout=5)
        info_data = info_response.json() if info_response.status_code == 200 else None
        
        return {
            "status": "healthy" if health_data else "unhealthy",
            "health_data": health_data,
            "info_data": info_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def print_status_summary(status_data):
    """Print formatted status summary"""
    print("🔍 OCR API Status Check")
    print("=" * 40)
    print(f"Timestamp: {status_data['timestamp']}")
    print(f"Overall Status: {status_data['status'].upper()}")
    
    if status_data['status'] == 'healthy':
        health = status_data['health_data']
        info = status_data['info_data']
        
        print(f"API Status: {health.get('status', 'Unknown')}")
        print(f"Active Tasks: {health.get('active_tasks', 'Unknown')}")
        print(f"API Version: {info.get('version', 'Unknown')}")
        print(f"Available Endpoints:")
        for endpoint, path in info.get('endpoints', {}).items():
            print(f"  - {endpoint}: {path}")
        
        print("\n✅ API is healthy and ready for requests")
    elif status_data['status'] == 'error':
        print(f"❌ Error: {status_data['error']}")
    else:
        print("❌ API is not responding properly")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR API Status Check")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch mode - check every 5 seconds")
    
    args = parser.parse_args()
    
    if args.watch:
        print("🔄 Watching API status (Ctrl+C to stop)...")
        try:
            while True:
                status = check_api_status(args.url)
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ", end="")
                print_status_summary(status)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 Stopped watching")
    else:
        status = check_api_status(args.url)
        print_status_summary(status)

if __name__ == "__main__":
    main()
