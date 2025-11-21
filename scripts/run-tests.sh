#!/bin/bash

echo "🧪 Running La Escoba Backend Tests..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_status "❌ Docker is not running. Please start Docker first." "$RED"
    exit 1
fi

print_status "🚀 Building and starting services..." "$YELLOW"
docker compose down
docker compose up --build -d

print_status "⏳ Waiting for services to be ready..." "$YELLOW"
sleep 15

print_status "🏥 Running health checks..." "$YELLOW"

# Health check function
check_service() {
    local service_name=$1
    local service_path=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000${service_path}")
        
        if [ "$response" -eq 200 ]; then
            print_status "✅ $service_name: HEALTHY" "$GREEN"
            return 0
        else
            print_status "⏳ $service_name: Waiting... (attempt $attempt/$max_attempts)" "$YELLOW"
            sleep 3
            ((attempt++))
        fi
    done
    
    print_status "❌ $service_name: FAILED to start" "$RED"
    return 1
}

# Check all services
check_service "API Gateway" "/health"
check_service "Auth Service" "/auth/health"
check_service "Cards Service" "/cards/health"
check_service "Matches Service" "/matches/health"

print_status "🔗 Running integration tests..." "$YELLOW"
if [ -d "test/integration" ]; then
    cd test/integration
    if python test_api_gateway.py; then
        print_status "✅ API Gateway tests passed" "$GREEN"
    else
        print_status "❌ API Gateway tests failed" "$RED"
    fi
    
    if python test_end_to_end.py; then
        print_status "✅ End-to-end tests passed" "$GREEN"
    else
        print_status "❌ End-to-end tests failed" "$RED"
    fi
    cd ../..
else
    print_status "ℹ️ Integration tests directory not found, skipping." "$YELLOW"
fi

print_status "📮 Running Postman tests..." "$YELLOW"
if command -v newman &> /dev/null; then
    for collection in test/postman/*.json; do
        if [ -f "$collection" ]; then
            service_name=$(basename "$collection" | sed 's/-tests.json//')
            print_status "Testing $service_name..." "$YELLOW"
            if newman run "$collection"; then
                print_status "✅ $service_name Postman tests passed" "$GREEN"
            else
                print_status "❌ $service_name Postman tests failed" "$RED"
            fi
        fi
    done
else
    print_status "ℹ️ Newman not installed. Skipping Postman tests." "$YELLOW"
    print_status "Install with: npm install -g newman" "$YELLOW"
fi

print_status "🐝 Starting Locust performance tests..." "$YELLOW"
if [ -f "test/locust/locustfile.py" ]; then
    cd test/locust
    locust -f locustfile.py --headless -u 10 -r 5 -t 30s --host=http://localhost:5000 &
    LOCUST_PID=$!
    cd ../..
    
    print_status "⏳ Running performance tests for 30 seconds..." "$YELLOW"
    sleep 35
    
    if ps -p $LOCUST_PID > /dev/null; then
        kill $LOCUST_PID
        print_status "✅ Performance tests completed" "$GREEN"
    else
        print_status "✅ Performance tests finished" "$GREEN"
    fi
else
    print_status "ℹ️ Locust tests not found, skipping." "$YELLOW"
fi

print_status "🛑 Stopping services..." "$YELLOW"
docker compose down

print_status "🎉 Test execution completed!" "$GREEN"
print_status "📊 For detailed performance testing, run: cd test/locust && locust -f locustfile.py" "$GREEN"
