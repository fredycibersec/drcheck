#!/bin/bash

# Domain Reputation WebApp - Setup Script
# Automatic installation and configuration

set -e  # Exit on error

echo "🔍 Domain Reputation WebApp - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please do not run this script as root${NC}"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher:"
    echo "  sudo apt-get install python3 python3-pip python3-venv  # Debian/Ubuntu"
    echo "  sudo yum install python3 python3-pip  # RHEL/CentOS"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed${NC}"
    echo "Installing pip..."
    sudo apt-get install python3-pip -y || sudo yum install python3-pip -y
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "📁 Project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists, skipping...${NC}"
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    chmod 600 .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys:"
echo "     nano .env"
echo ""
echo "  2. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  3. Run the application:"
echo "     python app.py"
echo ""
echo "  4. Open your browser at:"
echo "     http://localhost:5000"
echo ""
echo "Optional: Install as a systemd service:"
echo "  sudo ./scripts/install-service.sh"
echo "=========================================="
