#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Romega Chatbot - Local Testing Script${NC}\n"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your GOOGLE_API_KEY${NC}"
    echo -e "${YELLOW}Get your key from: https://aistudio.google.com/app/apikey${NC}"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=.*[^=]$" .env; then
    echo -e "${RED}❌ GOOGLE_API_KEY not set in .env file${NC}"
    echo -e "${YELLOW}Please edit .env and add your API key${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment file found${NC}\n"

# Function to test API endpoint
test_endpoint() {
    local url=$1
    local method=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: ${description}${NC}"
    echo -e "Endpoint: ${method} ${url}\n"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${url}")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "${url}" \
            -H "Content-Type: application/json" \
            -d "${data}")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}✅ Success (${http_code})${NC}"
        echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Failed (${http_code})${NC}"
        echo "$body"
    fi
    
    echo -e "\n${'─'*60}\n"
}

# Wait for API to be ready
echo -e "${YELLOW}Waiting for API to start...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is ready!${NC}\n"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}❌ API failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker logs romega-chatbot${NC}"
    exit 1
fi

echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  Testing Romega Chatbot API${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}\n"

# Test endpoints
test_endpoint "http://localhost:8000/" "GET" "" "Root endpoint"
test_endpoint "http://localhost:8000/health" "GET" "" "Health check"
test_endpoint "http://localhost:8000/chat" "POST" '{"message":"What services does Romega offer?"}' "Chat - Services question"
test_endpoint "http://localhost:8000/chat" "POST" '{"message":"How much does RPO cost?"}' "Chat - Pricing question"
test_endpoint "http://localhost:8000/chat" "POST" '{"message":"Who founded Romega?"}' "Chat - Company info"

echo -e "${GREEN}✅ All tests completed!${NC}\n"
echo -e "${YELLOW}📖 View interactive API docs at: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}📚 View ReDoc at: http://localhost:8000/redoc${NC}"
