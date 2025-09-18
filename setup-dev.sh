#!/bin/bash
# OpenMoxie Development Environment Setup Script

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up OpenMoxie Development Environment${NC}"

# Check Python version
echo -e "${YELLOW}🐍 Checking Python version...${NC}"
if ! python3.12 --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Python 3.12 is required but not found.${NC}"
    echo -e "${YELLOW}💡 Install Python 3.12 or use pyenv:${NC}"
    echo -e "   brew install python@3.12"
    echo -e "   # or"
    echo -e "   pyenv install 3.12.11"
    exit 1
fi

echo -e "${GREEN}✅ Python 3.12 found${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3.12 -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check Docker
echo -e "${YELLOW}🐳 Checking Docker...${NC}"
if ! docker --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is required but not found.${NC}"
    echo -e "${YELLOW}💡 Install Docker Desktop from: https://www.docker.com/products/docker-desktop/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Setup environment variables
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📄 Setting up environment variables...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Copied .env.example to .env${NC}"
        echo -e "${YELLOW}💡 Edit .env file to add your OpenAI API key and other settings${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Django setup
echo -e "${YELLOW}💾 Setting up Django database...${NC}"
python site/manage.py migrate

echo -e "${YELLOW}💾 Initializing data...${NC}"
python site/manage.py init_data

# Make scripts executable
chmod +x dev-start.sh
chmod +x dev-stop.sh

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "   1. Edit .env file with your OpenAI API key"
echo -e "   2. Run: ${GREEN}./dev-start.sh${NC} to start development server"
echo -e "   3. Visit: ${BLUE}http://localhost:8000/hive${NC}"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo -e "   ${GREEN}./dev-start.sh${NC}  - Start development environment"
echo -e "   ${GREEN}./dev-stop.sh${NC}   - Stop all services"
echo -e "   ${GREEN}source venv/bin/activate${NC} - Activate Python environment"