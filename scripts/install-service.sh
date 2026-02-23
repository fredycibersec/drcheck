#!/bin/bash

# Domain Reputation WebApp - Service Installation Script
# Installs the application as a systemd service

set -e  # Exit on error

echo "🔍 Domain Reputation WebApp - Service Installer"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Get real user (not root)
REAL_USER="${SUDO_USER:-$USER}"
if [ "$REAL_USER" = "root" ]; then
    echo -e "${RED}❌ Please run this script with sudo, not as root directly${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REAL_HOME=$(eval echo ~$REAL_USER)

echo "📁 Project directory: $PROJECT_DIR"
echo "👤 Running as user: $REAL_USER"
echo "🏠 Home directory: $REAL_HOME"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "The service will look for environment variables in flask-app.env"
fi

# Create flask-app.env from .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "📝 Creating flask-app.env from .env..."
    cp "$PROJECT_DIR/.env" "$PROJECT_DIR/flask-app.env"
    chown $REAL_USER:$REAL_USER "$PROJECT_DIR/flask-app.env"
    chmod 600 "$PROJECT_DIR/flask-app.env"
    echo -e "${GREEN}✅ flask-app.env created${NC}"
else
    echo -e "${YELLOW}⚠️  Please create flask-app.env manually with your API keys${NC}"
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/domain-reputation-webapp.service"

echo ""
echo "📄 Creating systemd service file..."

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Domain Reputation WebApp Flask Service
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/flask-app.env
ExecStart=$PROJECT_DIR/venv/bin/python3 app.py
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service file created at $SERVICE_FILE${NC}"

# Reload systemd
echo ""
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload
echo -e "${GREEN}✅ Systemd reloaded${NC}"

# Enable service
echo ""
echo "🔧 Enabling service..."
systemctl enable domain-reputation-webapp.service
echo -e "${GREEN}✅ Service enabled${NC}"

# Start service
echo ""
echo "🚀 Starting service..."
systemctl start domain-reputation-webapp.service
sleep 2

# Check status
echo ""
echo "📊 Service status:"
systemctl status domain-reputation-webapp.service --no-pager || true

echo ""
echo "================================================"
echo -e "${GREEN}🎉 Service installation completed!${NC}"
echo ""
echo "Useful commands:"
echo "  • View status:    sudo systemctl status domain-reputation-webapp"
echo "  • Restart:        sudo systemctl restart domain-reputation-webapp"
echo "  • Stop:           sudo systemctl stop domain-reputation-webapp"
echo "  • View logs:      sudo journalctl -u domain-reputation-webapp -f"
echo "  • Disable:        sudo systemctl disable domain-reputation-webapp"
echo ""
echo "Access the application at: http://localhost:5000"
echo "================================================"
