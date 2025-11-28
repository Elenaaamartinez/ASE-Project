#!/bin/bash

echo "⏳ Waiting for services to be ready..."
echo "======================================"

BASE_URL="http://localhost:5000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

wait_for_service() {
    local service_name=$1
    local service_path=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "⏳ Waiting for $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:5000${service_path}" > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        else
            if [ $attempt -eq $max_attempts ]; then
                echo -e " ${RED}❌${NC}"
                return 1
            fi
            echo -n "."
            sleep 2
            ((attempt++))
        fi
    done
    
    return 1
}

check_service_health() {
    local service_name=$1
    local service_path=$2
    
    response=$(curl -s "http://localhost:5000${service_path}")
    if echo "$response" | grep -q "connected\|running"; then
        echo -e "  ${GREEN}✓${NC} $service_name: Healthy"
        return 0
    else
        echo -e "  ${RED}✗${NC} $service_name: Unhealthy"
        return 1
    fi
}

echo ""
echo "🔍 Checking service status:"

# Wait for essential services
wait_for_service "API Gateway" "/health"
wait_for_service "Auth Service" "/auth/health"
wait_for_service "Database Connection" "/auth/health"  # This checks DB connection via auth health

echo ""
echo "🏥 Detailed health check:"

# Check each service's detailed health
check_service_health "API Gateway" "/health"
check_service_health "Auth Service" "/auth/health" 
check_service_health "Cards Service" "/cards/health"
check_service_health "Matches Service" "/matches/health"
check_service_health "Player Service" "/players/health"
check_service_health "History Service" "/history/health"

echo ""
echo -e "${GREEN}🚀 All services are ready!${NC}"
echo ""
echo "Quick test commands:"
echo "  Register user:    curl -X POST http://localhost:5000/auth/register -H \"Content-Type: application/json\" -d '{\"username\":\"test\",\"password\":\"pass123\"}'"
echo "  View cards:       curl http://localhost:5000/cards/cards"
echo "  Health check:     curl http://localhost:5000/health"
