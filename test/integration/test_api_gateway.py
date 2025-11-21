#!/usr/bin/env python3
"""
Simple API Gateway integration test
Runs inside Docker container - no external dependencies needed
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test API Gateway health endpoint"""
    print("🧪 Testing API Gateway health...")
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert "API Gateway is running" in response.json()["status"]
    print("✅ Health check passed")

def test_cards_service():
    """Test cards service routing"""
    print("🧪 Testing cards service...")
    response = requests.get(f"{BASE_URL}/cards/cards", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) == 40
    print("✅ Cards service passed")

def test_matches_service():
    """Test matches service routing"""
    print("🧪 Testing matches service...")
    response = requests.post(
        f"{BASE_URL}/matches/matches",
        json={"player1": "test1", "player2": "test2"},
        timeout=5
    )
    assert response.status_code == 201
    data = response.json()
    assert "match_id" in data
    print("✅ Matches service passed")

def main():
    """Run all tests"""
    try:
        test_health_check()
        test_cards_service()
        test_matches_service()
        print("🎉 All API Gateway tests passed!")
        return 0
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
