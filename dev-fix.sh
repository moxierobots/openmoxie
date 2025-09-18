#!/bin/bash
# OpenMoxie Code Formatting Fix Script

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛠️  Fixing OpenMoxie Code Formatting${NC}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment not found. Run setup-dev.sh first.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "site/manage.py" ]; then
    echo -e "${RED}❌ Not in OpenMoxie project root directory${NC}"
    exit 1
fi

# Format code with Black
echo -e "${YELLOW}🎨 Formatting code with Black...${NC}"
black site/

# Sort imports with isort
echo -e "${YELLOW}📦 Sorting imports with isort...${NC}"
isort site/

echo -e "${GREEN}✅ Code formatting completed${NC}"
echo -e "${BLUE}💡 Run ./dev-check.sh to verify all quality checks pass${NC}"