#!/bin/bash

# Domain Reputation WebApp - Service Installation Script
# Installs the application as a systemd service

SERVICE_NAME="domain-reputation-webapp"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PORT=5000

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── helpers ──────────────────────────────────────────────────────────────────

ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}"; }
info() { echo -e "${BLUE}ℹ️  $*${NC}"; }

# ── uninstall mode ────────────────────────────────────────────────────────────

uninstall() {
    echo ""
    echo -e "${YELLOW}Uninstalling ${SERVICE_NAME}...${NC}"
    echo ""

    if ! systemctl list-unit-files "${SERVICE_NAME}.service" &>/dev/null; then
        warn "Service not found, nothing to uninstall."
        exit 0
    fi

    systemctl stop    "${SERVICE_NAME}.service" 2>/dev/null && ok "Service stopped"   || true
    systemctl disable "${SERVICE_NAME}.service" 2>/dev/null && ok "Service disabled"  || true

    if [ -f "$SERVICE_FILE" ]; then
        rm "$SERVICE_FILE"
        systemctl daemon-reload
        ok "Service file removed"
    fi

    echo ""
    ok "Uninstall complete."
    exit 0
}

if [[ "$1" == "--uninstall" ]]; then
    if [ "$EUID" -ne 0 ]; then err "Run with sudo to uninstall."; exit 1; fi
    uninstall
fi

# ── install mode ──────────────────────────────────────────────────────────────

echo ""
echo "🔍 Domain Reputation WebApp — Service Installer"
echo "================================================"
echo ""

# Must run via sudo (not directly as root)
if [ "$EUID" -ne 0 ]; then
    err "This script must be run with sudo."
    exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
if [ "$REAL_USER" = "root" ]; then
    err "Please run with sudo, not as root directly."
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "  Project : $PROJECT_DIR"
echo "  User    : $REAL_USER"
echo "  Port    : $PORT"
echo ""

# 1 ── venv check ─────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/venv/bin/python3" ]; then
    err "Virtual environment not found at $PROJECT_DIR/venv/"
    echo ""
    echo "  Run setup first:"
    echo "    bash $PROJECT_DIR/scripts/setup.sh"
    echo ""
    exit 1
fi
ok "Virtual environment found"

# 2 ── .env check ─────────────────────────────────────────────────────────────
ENV_FILE=""
if [ -f "$PROJECT_DIR/.env" ]; then
    ENV_FILE="$PROJECT_DIR/.env"
    ok ".env file found"
else
    warn ".env not found — service will start without API keys."
    echo "     Configure keys later via the web UI (http://localhost:${PORT})."
fi

# 3 ── port availability check ────────────────────────────────────────────────
if ss -tlnp 2>/dev/null | grep -q ":${PORT} " || lsof -i ":${PORT}" &>/dev/null 2>&1; then
    warn "Port ${PORT} is already in use."
    OWNER=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1)
    [ -n "$OWNER" ] && info "Held by PID $OWNER ($(cat /proc/$OWNER/comm 2>/dev/null || echo unknown))"
    echo ""
    read -r -p "  Continue anyway? The service will fail until port is free. [y/N] " REPLY
    [[ "$REPLY" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

# 4 ── existing service check ─────────────────────────────────────────────────
if [ -f "$SERVICE_FILE" ]; then
    warn "Service already installed at $SERVICE_FILE"
    echo ""
    read -r -p "  Overwrite and reinstall? [y/N] " REPLY
    [[ "$REPLY" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
    echo ""
    systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
fi

# 5 ── write service file ──────────────────────────────────────────────────────
echo ""
info "Creating systemd service file..."

# Build EnvironmentFile line only when .env exists
ENV_LINE=""
[ -n "$ENV_FILE" ] && ENV_LINE="EnvironmentFile=${ENV_FILE}"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Domain Reputation WebApp Flask Service
After=network.target

[Service]
Type=simple
User=${REAL_USER}
WorkingDirectory=${PROJECT_DIR}
${ENV_LINE}
ExecStart=${PROJECT_DIR}/venv/bin/python3 app.py
Restart=on-failure
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${PROJECT_DIR}
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF

ok "Service file created: $SERVICE_FILE"

# 6 ── enable & start ──────────────────────────────────────────────────────────
echo ""
info "Reloading systemd daemon..."
systemctl daemon-reload

info "Enabling service..."
systemctl enable "${SERVICE_NAME}.service"

info "Starting service..."
systemctl start "${SERVICE_NAME}.service"

# 7 ── verify startup ──────────────────────────────────────────────────────────
echo ""
info "Waiting for service to stabilise..."
sleep 3

if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
    ok "Service is running on http://localhost:${PORT}"
else
    err "Service failed to start. Last journal entries:"
    echo ""
    journalctl -u "${SERVICE_NAME}.service" -n 20 --no-pager
    echo ""
    err "Fix the issue above, then run: sudo systemctl start ${SERVICE_NAME}"
    exit 1
fi

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "================================================"
ok "Installation complete!"
echo ""
echo "  • Status  : sudo systemctl status  ${SERVICE_NAME}"
echo "  • Restart : sudo systemctl restart ${SERVICE_NAME}"
echo "  • Stop    : sudo systemctl stop    ${SERVICE_NAME}"
echo "  • Logs    : sudo journalctl -u ${SERVICE_NAME} -f"
echo "  • Remove  : sudo bash scripts/install-service.sh --uninstall"
echo ""
echo "  Access: http://localhost:${PORT}"
echo "================================================"
echo ""
