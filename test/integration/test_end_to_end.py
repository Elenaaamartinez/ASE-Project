import requests
import pytest
import time
import uuid

BASE_URL = "http://localhost:5000"

class TestEndToEnd:
    """End-to-end tests for complete game flow"""
    
    def test_complete_game_flow(self):
        """Test complete game flow from registration to gameplay"""
        timestamp = int(time.time())
        
        # 1. Register players
        player1_data = {
            "username": f"e2e_player1_{timestamp}",
            "password": "password123",
            "email": f"e2e1_{timestamp}@test.com"
        }
        
        player2_data = {
            "username": f"e2e_player2_{timestamp}", 
            "password": "password123",
            "email": f"e2e2_{timestamp}@test.com"
        }
        
        # Register player 1
        response1 = requests.post(f"{BASE_URL}/auth/register", json=player1_data)
        assert response1.status_code == 201
        
        # Register player 2
        response2 = requests.post(f"{BASE_URL}/auth/register", json=player2_data)
        assert response2.status_code == 201
        
        # 2. View cards
        cards_response = requests.get(f"{BASE_URL}/cards/cards")
        assert cards_response.status_code == 200
        cards_data = cards_response.json()
        assert len(cards_data["cards"]) > 0
        
        # 3. Create match
        match_response = requests.post(
            f"{BASE_URL}/matches/matches",
            json={
                "player1": player1_data["username"],
                "player2": player2_data["username"]
            }
        )
        assert match_response.status_code == 201
        match_data = match_response.json()
        match_id = match_data["match_id"]
        
        # 4. Get match state for both players
        state1_response = requests.get(f"{BASE_URL}/matches/matches/{match_id}?player={player1_data['username']}")
        assert state1_response.status_code == 200
        state1_data = state1_response.json()
        assert "your_hand" in state1_data
        
        state2_response = requests.get(f"{BASE_URL}/matches/matches/{match_id}?player={player2_data['username']}")
        assert state2_response.status_code == 200
        state2_data = state2_response.json()
        assert "your_hand" in state2_data
        
        print("✅ End-to-end test completed successfully!")
        print(f"Match ID: {match_id}")
        print(f"Player 1 hand: {state1_data.get('your_hand', [])}")
        print(f"Player 2 hand: {state2_data.get('your_hand', [])}")

def test_service_health_checks():
    """Test that all services are healthy"""
    services = ["/health", "/auth/health", "/cards/health", "/matches/health"]
    
    for service in services:
        response = requests.get(f"{BASE_URL}{service}")
        assert response.status_code == 200, f"Service {service} is not healthy"
        print(f"✅ {service} is healthy")

if __name__ == "__main__":
    # Run the tests
    test_end_to_end = TestEndToEnd()
    test_end_to_end.test_complete_game_flow()
    test_service_health_checks()
