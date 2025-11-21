#!/bin/bash

echo "🏥 Health Check for La Escoba Services"

BASE_URL="http://localhost:5000"
SERVICES=(
    "/health"
    "/auth/health" 
    "/cards/health"
    "/matches/health"
)

all_healthy=true

for service in "${SERVICES[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${service}")
    
    if [ "$response" -eq 200 ]; then
        echo "✅ $service: HEALTHY (HTTP $response)"
    else
        echo "❌ $service: UNHEALTHY (HTTP $response)"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "💥 Some services are unhealthy. Check the logs with: docker compose logs"
    exit 1
fi
