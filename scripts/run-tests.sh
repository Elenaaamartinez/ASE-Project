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

# Build and start services
print_status "🚀 Building and starting services..." "$YELLOW"
docker compose down
docker compose up --build -d

# Wait for services to be ready
print_status "⏳ Waiting for services to be ready..." "$YELLOW"
sleep 15

# Run health checks
print_status "🏥 Running health checks..." "$YELLOW"
curl -f http://localhost:5000/health || exit 1
curl -f http://localhost:5000/auth/health || exit 1
curl -f http://localhost:5000/cards/health || exit 1
curl -f http://localhost:5000/matches/health || exit 1

# Run integration tests if the directory exists
if [ -d "tests/integration" ]; then
    print_status "🔗 Running integration tests..." "$YELLOW"
    cd tests/integration
    python test_api_gateway.py
    python test_end_to_end.py
    cd ../..
else
    print_status "ℹ️ Integration tests directory not found, skipping." "$YELLOW"
fi

# Run Postman tests (if Newman is installed)
if command -v newman &> /dev/null; then
    print_status "📮 Running Postman tests..." "$YELLOW"
    for collection in tests/postman/*.json; do
        service_name=$(basename "$collection" | sed 's/-tests.json//')
        print_status "Testing $service_name..." "$YELLOW"
        newman run "$collection"
    done
else
    print_status "ℹ️ Newman not installed. Skipping Postman tests." "$YELLOW"
    print_status "Install with: npm install -g newman" "$YELLOW"
fi

# Run Locust tests in background
print_status "🐝 Starting Locust performance tests..." "$YELLOW"
cd tests/locust
locust -f locustfile.py --headless -u 10 -r 5 -t 30s &
LOCUST_PID=$!
cd ../..

print_status "✅ All tests completed!" "$GREEN"
print_status "📊 View Locust results at: http://localhost:8089" "$GREEN"

# Wait for Locust to finish
wait $LOCUST_PID

# Stop services
print_status "🛑 Stopping services..." "$YELLOW"
docker compose down
