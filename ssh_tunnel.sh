#!/bin/bash
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
