#!/bin/bash
# OpenMoxie Development Startup Script

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting OpenMoxie Development Environment${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run setup-dev.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Copy from .env.example and configure.${NC}"
    exit 1
fi

# Start MQTT broker in background
echo -e "${YELLOW}🔌 Starting MQTT broker...${NC}"
docker-compose up -d mqtt

# Wait a moment for MQTT to be ready
sleep 3

# Check if database needs setup
echo -e "${YELLOW}💾 Checking database...${NC}"
python site/manage.py migrate

# Start Django development server
echo -e "${GREEN}🌐 Starting Django development server...${NC}"
echo -e "${BLUE}📍 Web interface will be available at: http://localhost:8001/hive${NC}"
echo -e "${BLUE}📍 Django admin will be available at: http://localhost:8001/admin${NC}"
echo -e "${BLUE}📍 MQTT Dashboard will be available at: http://localhost:18083${NC}"

# Run with --noreload as mentioned in README
python site/manage.py runserver 0.0.0.0:8001 --noreload
