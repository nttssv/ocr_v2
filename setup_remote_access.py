#!/usr/bin/env python3
"""
Remote Access Setup Script

This script helps you set up remote access to the OCR API.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def check_api_status():
    """Check if API is running"""
    print("🔍 Checking API status...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running - Status: {data['status']}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not accessible: {e}")
        return False

def get_server_info():
    """Get server information"""
    print("📊 Getting server information...")
    
    # Get internal IP
    try:
        result = subprocess.run("hostname -I", shell=True, capture_output=True, text=True)
        internal_ip = result.stdout.strip().split()[0]
        print(f"🏠 Internal IP: {internal_ip}")
    except:
        print("❌ Could not get internal IP")
        internal_ip = "UNKNOWN"
    
    # Get external IP
    try:
        result = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True)
        external_ip = result.stdout.strip()
        if external_ip:
            print(f"🌍 External IP: {external_ip}")
        else:
            print("❌ Could not get external IP")
            external_ip = "UNKNOWN"
    except:
        print("❌ Could not get external IP")
        external_ip = "UNKNOWN"
    
    return internal_ip, external_ip

def create_access_scripts():
    """Create convenient access scripts"""
    print("📝 Creating access scripts...")
    
    # Create direct access script
    direct_script = """#!/bin/bash
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
        curl -X POST "$API_URL/documents/transform" \
            -F "file=@$2" \
            -F "language=vie" \
            -F "enable_handwriting_detection=false"
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
"""
    
    with open("direct_access.sh", "w") as f:
        f.write(direct_script)
    
    os.chmod("direct_access.sh", 0o755)
    print("✅ Created direct_access.sh")
    
    # Create SSH tunnel script
    tunnel_script = """#!/bin/bash
# SSH Tunnel Script for OCR API
# Usage: ./ssh_tunnel.sh [start|stop|status]

TUNNEL_PID_FILE="/tmp/ocr_tunnel.pid"
LOCAL_PORT="8000"
REMOTE_PORT="8000"
REMOTE_HOST="YOUR_SERVER_IP"  # Replace with your server IP
REMOTE_USER="gcpcoder"

case "$1" in
    "start")
        if [ -f "$TUNNEL_PID_FILE" ]; then
            echo "❌ Tunnel already running (PID: $(cat $TUNNEL_PID_FILE))"
            exit 1
        fi
        
        echo "🚀 Starting SSH tunnel..."
        ssh -f -N -L $LOCAL_PORT:localhost:$REMOTE_PORT $REMOTE_USER@$REMOTE_HOST
        echo $! > $TUNNEL_PID_FILE
        echo "✅ SSH tunnel started (PID: $(cat $TUNNEL_PID_FILE))"
        echo "🌐 API accessible at: http://localhost:8000"
        ;;
    "stop")
        if [ -f "$TUNNEL_PID_FILE" ]; then
            PID=$(cat $TUNNEL_PID_FILE)
            kill $PID 2>/dev/null
            rm -f $TUNNEL_PID_FILE
            echo "✅ SSH tunnel stopped"
        else
            echo "❌ No tunnel running"
        fi
        ;;
    "status")
        if [ -f "$TUNNEL_PID_FILE" ]; then
            PID=$(cat $TUNNEL_PID_FILE)
            if ps -p $PID > /dev/null 2>&1; then
                echo "✅ SSH tunnel is running (PID: $PID)"
            else
                echo "❌ SSH tunnel is not running"
                rm -f $TUNNEL_PID_FILE
            fi
        else
            echo "❌ No tunnel running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        echo ""
        echo "Before using, edit this script and set:"
        echo "  REMOTE_HOST - Your server's IP address"
        echo "  REMOTE_USER - Your SSH username"
        ;;
esac
"""
    
    with open("ssh_tunnel.sh", "w") as f:
        f.write(tunnel_script)
    
    os.chmod("ssh_tunnel.sh", 0o755)
    print("✅ Created ssh_tunnel.sh")
    
    # Create Python client requirements
    requirements = """requests>=2.28.0
rich>=13.0.0
"""
    
    with open("requirements_remote.txt", "w") as f:
        f.write(requirements)
    
    print("✅ Created requirements_remote.txt")

def main():
    """Main setup function"""
    print("🚀 OCR API Remote Access Setup")
    print("=" * 40)
    
    # Check if API is running
    if not check_api_status():
        print("\n❌ API is not running. Please start the API first:")
        print("   cd /home/gcpcoder/ocr_v2")
        print("   source ocr_env/bin/activate")
        print("   python api.py")
        return 1
    
    # Get server information
    internal_ip, external_ip = get_server_info()
    
    # Create access scripts
    create_access_scripts()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Access Methods:")
    print("1. Direct Access (if firewall allows):")
    print(f"   API URL: http://{internal_ip}:8000")
    print("   Use: python remote_client.py --url http://{internal_ip}:8000")
    
    print("\n2. SSH Tunnel (recommended):")
    print("   Edit ssh_tunnel.sh and set your server IP")
    print("   Run: ./ssh_tunnel.sh start")
    print("   Then use: python remote_client.py --url http://localhost:8000")
    
    print("\n3. Quick Commands:")
    print("   Health check: ./direct_access.sh health")
    print("   Upload file:  ./direct_access.sh upload your_file.pdf")
    print("   Check status: ./direct_access.sh status DOCUMENT_ID")
    
    print("\n📚 Documentation:")
    print("   - REMOTE_ACCESS_GUIDE.md - Complete setup guide")
    print("   - remote_client.py - Python client with examples")
    print("   - integration_test.py - API testing suite")
    
    print("\n🔧 Next Steps:")
    print("1. Copy the remote_client.py to your local computer")
    print("2. Install requirements: pip install -r requirements_remote.txt")
    print("3. Test connection: python remote_client.py --health")
    print("4. Process documents: python remote_client.py --file your_document.pdf")
    
    return 0

if __name__ == "__main__":
    exit(main())
