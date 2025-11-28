#!/bin/bash

echo "🔒 Testing Security Features"
echo "============================"

BASE_URL="http://localhost:5000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${2}${1}${NC}"
}

# Test 1: Registration with weak password
print_status "Testing password validation..." "$YELLOW"
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testweak", "password": "123"}')

if [ "$response" -eq 400 ]; then
    print_status "✅ Weak password rejected" "$GREEN"
else
    print_status "❌ Weak password accepted" "$RED"
fi

# Test 2: Access protected endpoint without token
print_status "Testing JWT protection..." "$YELLOW"
response=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/players/testuser")

if [ "$response" -eq 401 ]; then
    print_status "✅ Protected endpoint requires authentication" "$GREEN"
else
    print_status "❌ Protected endpoint accessible without token" "$RED"
fi

# Test 3: Register and login properly
print_status "Testing secure registration/login..." "$YELLOW"
register_response=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "secureuser", "password": "securepass123", "email": "secure@test.com"}')

if echo "$register_response" | grep -q "registered successfully"; then
    print_status "✅ Secure registration successful" "$GREEN"
    
    # Test login
    login_response=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "secureuser", "password": "securepass123"}')
    
    if echo "$login_response" | grep -q "token"; then
        print_status "✅ Secure login successful" "$GREEN"
        
        # Extract token
        token=$(echo "$login_response" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
        
        # Test protected endpoint with token
        player_response=$(curl -s -o /dev/null -w "%{http_code}" \
          -H "Authorization: Bearer $token" \
          "$BASE_URL/players/secureuser")
        
        if [ "$player_response" -eq 200 ]; then
            print_status "✅ Protected endpoint accessible with valid token" "$GREEN"
        else
            print_status "❌ Protected endpoint inaccessible with valid token" "$RED"
        fi
    else
        print_status "❌ Login failed" "$RED"
    fi
else
    print_status "❌ Registration failed" "$RED"
fi

# Test 4: Invalid token
print_status "Testing invalid token rejection..." "$YELLOW"
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer invalid-token-here" \
  "$BASE_URL/players/someuser")

if [ "$response" -eq 401 ]; then
    print_status "✅ Invalid token rejected" "$GREEN"
else
    print_status "❌ Invalid token accepted" "$RED"
fi

echo ""
print_status "🔒 Security tests completed!" "$GREEN"
