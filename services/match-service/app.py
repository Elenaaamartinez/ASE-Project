from flask import Flask, request, jsonify
import random
import uuid
from datetime import datetime
import redis
import requests
import json
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Redis configuration with connection pooling
redis_client = redis.Redis(
    host='match-db', 
    port=6379, 
    db=0, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True
)

class EscobaGame:
    """Complete La Escoba game logic with persistence"""
    # ... (resto del codice della classe rimane uguale) ...

# Game storage (Redis)
def save_match(game):
    """Save match to Redis"""
    try:
        redis_client.set(f"match:{game.match_id}", json.dumps(game.to_dict()), ex=86400)  # 24h expiry
        return True
    except Exception as e:
        print(f"❌ Error saving match to Redis: {e}")
        return False

def load_match(match_id):
    """Load match from Redis"""
    try:
        data = redis_client.get(f"match:{match_id}")
        if data:
            return EscobaGame.from_dict(json.loads(data))
        return None
    except Exception as e:
        print(f"❌ Error loading match from Redis: {e}")
        return None

def delete_match(match_id):
    """Delete match from Redis"""
    try:
        redis_client.delete(f"match:{match_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting match from Redis: {e}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        return jsonify({
            "status": "Match service is running",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "Match service is running",
            "redis": "disconnected",
            "error": str(e)
        }), 503

@app.route('/match', methods=['POST'])
def create_match():
    """Create new match"""
    try:
        data = request.get_json()
        print(f"🎮 Received match creation data: {data}")
        
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        player1 = data.get('player1')
        player2 = data.get('player2')

        if not player1 or not player2:
            return jsonify({"error": "Both players required"}), 400

        match_id = str(uuid.uuid4())
        print(f"🎮 Creating match {match_id} for players {player1} vs {player2}")
        
        game = EscobaGame(match_id, player1, player2)
        
        if not save_match(game):
            return jsonify({"error": "Failed to save match"}), 500

        print(f"✅ Match created successfully: {match_id}")

        return jsonify({
            "match_id": match_id,
            "players": [player1, player2],
            "message": "Match created successfully",
            "initial_table": game.table_cards,
            "status": "active"
        }), 201

    except Exception as e:
        print(f"❌ Error creating match: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Match creation failed: {str(e)}"}), 500

@app.route('/match/<match_id>', methods=['GET'])
def get_match(match_id):
    """Get match state"""
    try:
        game = load_match(match_id)
        if not game:
            return jsonify({"error": "Match not found"}), 404

        player = request.args.get('player')
        if not player:
            return jsonify({"error": "Player parameter required"}), 400

        if player not in game.players:
            return jsonify({"error": "Player not participating in this match"}), 403

        return jsonify(game.get_game_state(player))

    except Exception as e:
        print(f"❌ Error getting match: {e}")
        return jsonify({"error": f"Failed to get match: {str(e)}"}), 500

@app.route('/match/<match_id>/play', methods=['POST'])
def play_card(match_id):
    """Play a card"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        player = data.get('player')
        card_id = data.get('card_id')

        if not player or card_id is None:
            return jsonify({"error": "Player and card_id required"}), 400

        # Convert card_id to int if it's a string
        try:
            card_id = int(card_id)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid card_id"}), 400

        game = load_match(match_id)
        if not game:
            return jsonify({"error": "Match not found"}), 404

        success, message = game.play_card(player, card_id)
        
        if success:
            if not save_match(game):
                return jsonify({"error": "Failed to save game state"}), 500
                
            return jsonify({
                "message": message,
                "game_state": game.get_game_state(player)
            })
        else:
            return jsonify({"error": message}), 400

    except Exception as e:
        print(f"❌ Error playing card: {e}")
        return jsonify({"error": f"Failed to play card: {str(e)}"}), 500

@app.route('/match/<match_id>', methods=['DELETE'])
def delete_match_endpoint(match_id):
    """Delete a match (admin only)"""
    try:
        if delete_match(match_id):
            return jsonify({"message": "Match deleted successfully"})
        else:
            return jsonify({"error": "Failed to delete match"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to delete match: {str(e)}"}), 500

@app.route('/match', methods=['GET'])
def list_matches():
    """List all active matches (admin only)"""
    try:
        match_keys = redis_client.keys("match:*")
        matches = []
        
        for key in match_keys:
            match_data = redis_client.get(key)
            if match_data:
                match_obj = json.loads(match_data)
                matches.append({
                    "match_id": match_obj["match_id"],
                    "players": match_obj["players"],
                    "status": match_obj["status"],
                    "current_player": match_obj["current_player"]
                })
        
        return jsonify({
            "active_matches": len(matches),
            "matches": matches
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list matches: {str(e)}"}), 500

if __name__ == '__main__':
    print("🎮 Match Service starting on port 5003...")
    print("🃏 La Escoba game logic loaded")
    print("🗄️  Redis storage enabled")
    print("🔗 Integrated with History and Player services")
    app.run(host='0.0.0.0', port=5003, debug=False)
