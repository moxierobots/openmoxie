#!/bin/bash
# OpenMoxie Code Quality Check Script

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running OpenMoxie Code Quality Checks${NC}"

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
black site/ --check --diff || {
    echo -e "${YELLOW}⚠️  Code formatting issues found. Run 'black site/' to fix.${NC}"
}

# Sort imports with isort
echo -e "${YELLOW}📦 Checking import sorting with isort...${NC}"
isort site/ --check-only --diff || {
    echo -e "${YELLOW}⚠️  Import sorting issues found. Run 'isort site/' to fix.${NC}"
}

# Lint with flake8
echo -e "${YELLOW}🔍 Linting with flake8...${NC}"
flake8 site/

# Type checking with mypy
echo -e "${YELLOW}🔒 Type checking with mypy...${NC}"
mypy site/ || {
    echo -e "${YELLOW}⚠️  Type checking issues found.${NC}"
}

# Security scanning with bandit
echo -e "${YELLOW}🔐 Security scanning with bandit...${NC}"
bandit -r site/ -x site/*/migrations/ || {
    echo -e "${YELLOW}⚠️  Security issues found.${NC}"
}

# Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
cd site
python -m pytest --tb=short
cd ..

echo -e "${GREEN}✅ Code quality checks completed${NC}"