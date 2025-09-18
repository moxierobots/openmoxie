#!/bin/bash
# OpenMoxie Development Environment Stop Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping OpenMoxie Development Environment${NC}"

# Stop Docker services
echo -e "${YELLOW}🐳 Stopping Docker services...${NC}"
docker-compose down

# Stop any running Django processes
echo -e "${YELLOW}🔄 Stopping Django processes...${NC}"
pkill -f "manage.py runserver" || true

echo -e "${GREEN}✅ All services stopped${NC}"