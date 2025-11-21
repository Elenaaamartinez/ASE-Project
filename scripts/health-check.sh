#!/bin/bash

echo "🏥 Health Check for La Escoba Services"
echo "======================================"

BASE_URL="http://localhost:5000"
SERVICES=(
    "API Gateway:/health"
    "Auth Service:/auth/health" 
    "Cards Service:/cards/health"
    "Matches Service:/matches/health"
    "Player Service:/players/health"
    "History Service:/history/health"
)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

all_healthy=true

for service in "${SERVICES[@]}"; do
    IFS=':' read -r service_name service_path <<< "$service"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${service_path}")
    response_time=$(curl -s -o /dev/null -w "%{time_total}s" "${BASE_URL}${service_path}")
    
    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✅ $service_name: HEALTHY (HTTP $response, ${response_time})${NC}"
    elif [ "$response" -eq 000 ]; then
        echo -e "${RED}❌ $service_name: OFFLINE (No response)${NC}"
        all_healthy=false
    elif [ "$response" -eq 404 ]; then
        echo -e "${YELLOW}⚠️  $service_name: NOT FOUND (HTTP 404) - Service may not be implemented${NC}"
    else
        echo -e "${RED}❌ $service_name: UNHEALTHY (HTTP $response, ${response_time})${NC}"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 All essential services are healthy!${NC}"
    echo ""
    echo "Quick test commands:"
    echo "  Create a match:    curl -X POST http://localhost:5000/matches/matches -H \"Content-Type: application/json\" -d '{\"player1\":\"test1\",\"player2\":\"test2\"}'"
    echo "  View cards:        curl http://localhost:5000/cards/cards"
    echo "  View API docs:     Check docs/ directory"
    exit 0
else
    echo -e "${RED}💥 Some services are unhealthy.${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check if services are running: docker ps"
    echo "  2. View service logs: docker compose logs"
    echo "  3. Restart services: docker compose down && docker compose up --build"
    echo "  4. Check Docker network: docker network ls"
    exit 1
fi
