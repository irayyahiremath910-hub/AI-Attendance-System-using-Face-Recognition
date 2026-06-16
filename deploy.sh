#!/bin/bash
# Production deployment script

set -e

echo "================================"
echo "AI Attendance System - Deployment Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production file not found!${NC}"
    echo "Please create .env.production from .env.production template"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '#' | xargs)

echo -e "${YELLOW}Step 1: Checking system requirements...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Building Docker images...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Docker images built successfully${NC}"
echo ""

echo -e "${YELLOW}Step 3: Starting services...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

echo -e "${YELLOW}Step 4: Running database migrations...${NC}"
docker-compose exec -T web python manage.py migrate
echo -e "${GREEN}✓ Database migrations completed${NC}"
echo ""

echo -e "${YELLOW}Step 5: Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

echo -e "${YELLOW}Step 6: Running deployment checks...${NC}"
docker-compose exec -T web python manage.py check --deploy
echo -e "${GREEN}✓ Deployment checks passed${NC}"
echo ""

echo -e "${YELLOW}Step 7: Verifying service health...${NC}"
sleep 10
docker-compose ps
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Services running:"
echo "  - Web Application: http://localhost:8000"
echo "  - Database: localhost:5432"
echo "  - Nginx: http://localhost:80"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
