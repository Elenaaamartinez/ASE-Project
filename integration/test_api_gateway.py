import requests
import pytest
import time

BASE_URL = "http://localhost:5000"

class TestAPIGateway:
    """Integration tests for API Gateway"""
    
    def test_health_check(self):
        """Test API Gateway health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "API Gateway is running"
    
    def test_auth_service_routing(self):
        """Test that auth service requests are properly routed"""
        # Test register endpoint
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": f"testuser_{int(time.time())}",
                "password": "testpass123",
                "email": f"test_{int(time.time())}@test.com"
            }
        )
        assert response.status_code in [201, 400]  # 201 created or 400 if user exists
    
    def test_cards_service_routing(self):
        """Test that cards service requests are properly routed"""
        response = requests.get(f"{BASE_URL}/cards/cards")
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert len(data["cards"]) == 40  # Spanish deck has 40 cards
    
    def test_match_service_routing(self):
        """Test that match service requests are properly routed"""
        response = requests.post(
            f"{BASE_URL}/matches/matches",
            json={
                "player1": "integration_test_player1",
                "player2": "integration_test_player2"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "match_id" in data
        assert "players" in data
    
    def test_invalid_service_routing(self):
        """Test that invalid service routes return 404"""
        response = requests.get(f"{BASE_URL}/invalid/service")
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
