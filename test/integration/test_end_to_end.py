#!/usr/bin/env python3
"""
Simple end-to-end test
Runs inside Docker container - no external dependencies needed
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"

def test_complete_flow():
    """Test complete game flow"""
    print("🧪 Testing complete game flow...")
    
    # 1. View cards
    print("📋 Getting cards...")
    cards_response = requests.get(f"{BASE_URL}/cards/cards", timeout=5)
    assert cards_response.status_code == 200
    cards_data = cards_response.json()
    assert len(cards_data["cards"]) == 40
    print("✅ Cards retrieved")
    
    # 2. Create match
    print("🎮 Creating match...")
    timestamp = int(time.time())
    match_response = requests.post(
        f"{BASE_URL}/matches/matches",
        json={
            "player1": f"player1_{timestamp}",
            "player2": f"player2_{timestamp}"
        },
        timeout=5
    )
    assert match_response.status_code == 201
    match_data = match_response.json()
    match_id = match_data["match_id"]
    print(f"✅ Match created: {match_id}")
    
    # 3. Get match state
    print("📊 Getting match state...")
    state_response = requests.get(
        f"{BASE_URL}/matches/matches/{match_id}?player=player1_{timestamp}",
        timeout=5
    )
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert "your_hand" in state_data
    print("✅ Match state retrieved")
    
    print("🎉 Complete flow test passed!")

def main():
    """Run end-to-end test"""
    try:
        test_complete_flow()
        return 0
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
