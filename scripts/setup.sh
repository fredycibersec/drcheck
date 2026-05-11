#!/bin/bash

# Domain Reputation WebApp - Setup Script
# Automatic installation and configuration

PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=8

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}"; }
info() { echo -e "${BLUE}ℹ️  $*${NC}"; }

# ── flags ─────────────────────────────────────────────────────────────────────

RESET=0
[[ "$1" == "--reset" ]] && RESET=1

# ── root check ────────────────────────────────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
    err "Do not run this script as root."
    exit 1
fi

echo ""
echo "🔍 Domain Reputation WebApp — Setup"
echo "===================================="
echo ""

# ── paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "  Project : $PROJECT_DIR"
echo ""

# ── python version check ──────────────────────────────────────────────────────

info "Checking Python version..."

if ! command -v python3 &>/dev/null; then
    err "Python 3 is not installed."
    echo ""
    echo "  Install it with:"
    echo "    sudo apt-get install python3 python3-venv   # Debian/Ubuntu"
    echo "    sudo dnf install python3                    # Fedora/RHEL"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt "$PYTHON_MIN_MAJOR" ] || \
   { [ "$PY_MAJOR" -eq "$PYTHON_MIN_MAJOR" ] && [ "$PY_MINOR" -lt "$PYTHON_MIN_MINOR" ]; }; then
    err "Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ required, found ${PY_VERSION}."
    exit 1
fi

ok "Python ${PY_VERSION}"

# ── python-venv availability ──────────────────────────────────────────────────

if ! python3 -m venv --help &>/dev/null; then
    err "python3-venv module not available."
    echo ""
    echo "  Install it with:"
    echo "    sudo apt-get install python3-venv   # Debian/Ubuntu"
    echo "    sudo dnf install python3-venv       # Fedora/RHEL"
    exit 1
fi

# ── required files check ──────────────────────────────────────────────────────

for f in requirements.txt .env.example; do
    if [ ! -f "$PROJECT_DIR/$f" ]; then
        err "Required file not found: $PROJECT_DIR/$f"
        echo "  The repository may be incomplete. Try cloning again."
        exit 1
    fi
done
ok "Required files present"

# ── venv ──────────────────────────────────────────────────────────────────────

echo ""
if [ "$RESET" -eq 1 ] && [ -d "$PROJECT_DIR/venv" ]; then
    warn "--reset: removing existing virtual environment..."
    rm -rf "$PROJECT_DIR/venv"
fi

if [ -d "$PROJECT_DIR/venv" ]; then
    warn "Virtual environment already exists (use --reset to reinstall from scratch)"
else
    info "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
    ok "Virtual environment created"
fi

# ── dependencies ──────────────────────────────────────────────────────────────

echo ""
info "Installing dependencies..."

# Upgrade pip only when creating a fresh venv (skip on reinstall to save time)
if [ "$RESET" -eq 1 ] || [ ! -f "$PROJECT_DIR/venv/bin/pip" ]; then
    "$PROJECT_DIR/venv/bin/pip" install --upgrade pip -q
fi

if ! "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q; then
    err "Dependency installation failed."
    echo "  Run manually for details:"
    echo "    source $PROJECT_DIR/venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
ok "Dependencies installed"

# ── verify installation ───────────────────────────────────────────────────────

echo ""
info "Verifying installation..."

if ! "$PROJECT_DIR/venv/bin/python3" -c "from flask import Flask; from cryptography.fernet import Fernet" 2>/dev/null; then
    err "Installation verification failed — key packages not importable."
    echo "  Try: $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
    exit 1
fi
ok "Installation verified"

# ── .env ──────────────────────────────────────────────────────────────────────

echo ""
if [ -f "$PROJECT_DIR/.env" ]; then
    warn ".env already exists — skipping (delete it manually to regenerate)"
else
    info "Creating .env from template..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    ok ".env created — edit it with your API keys before running the app"
fi

# ── summary ───────────────────────────────────────────────────────────────────

echo ""
echo "===================================="
ok "Setup complete!"
echo ""
echo "  Next steps:"
echo ""
if [ ! -s "$PROJECT_DIR/.env" ] || grep -q "your_.*_here" "$PROJECT_DIR/.env" 2>/dev/null; then
    echo "  1. Add your API keys:"
    echo "       nano $PROJECT_DIR/.env"
    echo ""
    echo "  2. Run the application:"
else
    echo "  1. Run the application:"
fi
echo "       source $PROJECT_DIR/venv/bin/activate"
echo "       python $PROJECT_DIR/app.py"
echo ""
echo "  Or install as a system service (autostart on boot):"
echo "       sudo bash $PROJECT_DIR/scripts/install-service.sh"
echo ""
echo "  Access: http://localhost:5000"
echo "===================================="
echo ""
