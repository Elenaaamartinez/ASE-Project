from flask import Flask, request, jsonify
import random
import uuid
from datetime import datetime
import redis
import requests
import json
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

# Redis configuration with better error handling
def get_redis_client():
    """Get Redis client with retry logic"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            client = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'match-db'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            client.ping()
            print("✅ Redis connection successful")
            return client
        except redis.ConnectionError as e:
            if i < max_retries - 1:
                print(f"⏳ Redis not ready, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"❌ Failed to connect to Redis after {max_retries} attempts")
                raise

redis_client = None

class EscobaGame:
    """Complete La Escoba game logic"""
    
    def __init__(self, match_id, player1, player2):
        self.match_id = match_id
        self.players = [player1, player2]
        self.current_player_index = 0
        self.status = "active"
        
        # Create and shuffle deck (cards 1-40)
        self.deck = list(range(1, 41))
        random.shuffle(self.deck)
        
        # Initialize game state
        self.hands = {player1: [], player2: []}
        self.table_cards = []
        self.captured = {player1: [], player2: []}
        self.scores = {player1: 0, player2: 0}
        self.escobas = {player1: 0, player2: 0}
        
        # Deal initial cards
        self._deal_initial_cards()
        
        self.created_at = datetime.now().isoformat()
        self.last_move = None
    
    def _deal_initial_cards(self):
        """Deal 3 cards to each player and 4 to table"""
        # 4 cards on table
        for _ in range(4):
            if self.deck:
                self.table_cards.append(self.deck.pop())
        
        # 3 cards to each player
        for _ in range(3):
            for player in self.players:
                if self.deck:
                    self.hands[player].append(self.deck.pop())
    
    def _refill_hands(self):
        """Refill hands to 3 cards each"""
        for player in self.players:
            while len(self.hands[player]) < 3 and self.deck:
                self.hands[player].append(self.deck.pop())
    
    def _get_card_value(self, card_id):
        """Get numeric value for a card (for sum to 15)"""
        value = ((card_id - 1) % 10) + 1
        if value == 8:  # Sota
            return 8
        elif value == 9:  # Caballo
            return 9
        elif value == 10:  # Rey
            return 10
        return value
    
    def _check_win_conditions(self):
        """Check if game should end and calculate final score"""
        # Game ends when deck is empty and all hands are empty
        if len(self.deck) == 0 and all(len(hand) == 0 for hand in self.hands.values()):
            self.status = "finished"
            
            # Last player to capture gets remaining table cards
            if self.table_cards and self.last_move:
                self.captured[self.last_move].extend(self.table_cards)
                self.table_cards = []
            
            # Calculate final scores
            for player in self.players:
                score = 0
                
                # Escobas
                score += self.escobas[player]
                
                # Most cards
                if len(self.captured[player]) > len(self.captured[self.players[0] if player == self.players[1] else self.players[1]]):
                    score += 1
                
                # Count coins (Oros)
                player_coins = sum(1 for card in self.captured[player] if 1 <= card <= 10)
                opponent = self.players[0] if player == self.players[1] else self.players[1]
                opponent_coins = sum(1 for card in self.captured[opponent] if 1 <= card <= 10)
                if player_coins > opponent_coins:
                    score += 1
                
                # 7 of Oros
                if 7 in self.captured[player]:
                    score += 1
                
                # 7 of Copas  
                if 17 in self.captured[player]:
                    score += 1
                
                self.scores[player] = score
    
    @property
    def current_player(self):
        return self.players[self.current_player_index]
    
    def play_card(self, player, card_id):
        """Play a card from hand"""
        if self.status != "active":
            return False, "Game is not active"
        
        if player != self.current_player:
            return False, f"Not your turn. Current player: {self.current_player}"
        
        if card_id not in self.hands[player]:
            return False, "Card not in hand"
        
        # Remove card from hand
        self.hands[player].remove(card_id)
        card_value = self._get_card_value(card_id)
        
        # Try to capture cards that sum to 15
        captured_cards = []
        table_values = {c: self._get_card_value(c) for c in self.table_cards}
        
        # Check all combinations for sum = 15
        can_capture = False
        for i in range(1, 2**len(self.table_cards)):
            combo = [self.table_cards[j] for j in range(len(self.table_cards)) if i & (1 << j)]
            if sum(table_values[c] for c in combo) + card_value == 15:
                captured_cards = combo
                can_capture = True
                break
        
        if can_capture:
            # Capture cards
            captured_cards.append(card_id)
            self.captured[player].extend(captured_cards)
            
            for card in captured_cards:
                if card in self.table_cards:
                    self.table_cards.remove(card)
            
            # Check for escoba (table is now empty)
            if len(self.table_cards) == 0 and len(self.deck) > 0:
                self.escobas[player] += 1
                message = f"Escoba! {player} captured all cards"
            else:
                message = f"{player} captured {len(captured_cards)} cards"
        else:
            # No capture - card stays on table
            self.table_cards.append(card_id)
            message = f"{player} placed card on table"
        
        self.last_move = player
        
        # Switch player
        self.current_player_index = 1 - self.current_player_index
        
        # Refill hands if needed
        self._refill_hands()
        
        # Check win conditions
        self._check_win_conditions()
        
        return True, message
    
    def get_game_state(self, requesting_player):
        """Get game state for a specific player"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.current_player,
            "your_hand": self.hands.get(requesting_player, []),
            "table_cards": self.table_cards,
            "captured_cards": self.captured.get(requesting_player, []),
            "scores": self.scores,
            "escobas": self.escobas,
            "status": self.status,
            "remaining_deck": len(self.deck),
            "opponent_hand_size": len(self.hands[self.players[0] if requesting_player == self.players[1] else self.players[1]])
        }
    
    def to_dict(self):
        """Serialize game to dict"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player_index": self.current_player_index,
            "status": self.status,
            "deck": self.deck,
            "hands": self.hands,
            "table_cards": self.table_cards,
            "captured": self.captured,
            "scores": self.scores,
            "escobas": self.escobas,
            "created_at": self.created_at,
            "last_move": self.last_move
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize game from dict"""
        game = cls.__new__(cls)
        game.match_id = data["match_id"]
        game.players = data["players"]
        game.current_player_index = data["current_player_index"]
        game.status = data["status"]
        game.deck = data["deck"]
        game.hands = data["hands"]
        game.table_cards = data["table_cards"]
        game.captured = data["captured"]
        game.scores = data["scores"]
        game.escobas = data["escobas"]
        game.created_at = data["created_at"]
        game.last_move = data.get("last_move")
        return game

# Game storage (Redis)
def save_match(game):
    """Save match to Redis"""
    try:
        if redis_client is None:
            return False
        redis_client.set(f"match:{game.match_id}", json.dumps(game.to_dict()), ex=86400)
        return True
    except Exception as e:
        print(f"❌ Error saving match to Redis: {e}")
        return False

def load_match(match_id):
    """Load match from Redis"""
    try:
        if redis_client is None:
            return None
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
        if redis_client is None:
            return False
        redis_client.delete(f"match:{match_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting match from Redis: {e}")
        return False

def save_match_to_history(game):
    """Save finished match to History Service"""
    if game.status != "finished":
        return
    
    try:
        history_service_url = os.environ.get('HISTORY_SERVICE_URL', 'http://history-service:5005')
        
        # Determine winner
        winner = max(game.scores, key=game.scores.get)
        if game.scores[game.players[0]] == game.scores[game.players[1]]:
            winner = "draw"
        
        match_data = {
            "match_id": game.match_id,
            "player1": game.players[0],
            "player2": game.players[1],
            "winner": winner,
            "scores": game.scores,
            "start_time": game.created_at,
            "end_time": datetime.now().isoformat(),
            "moves": []
        }
        
        response = requests.post(
            f"{history_service_url}/history/matches",
            json=match_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ Match {game.match_id} saved to history")
        else:
            print(f"⚠️ Failed to save match to history: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Could not save to history service: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        if redis_client:
            redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "disconnected"
        return jsonify({
            "status": "Match service is running",
            "redis": redis_status,
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
        
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        player1 = data.get('player1')
        player2 = data.get('player2')

        if not player1 or not player2:
            return jsonify({"error": "Both players required"}), 400

        match_id = str(uuid.uuid4())
        print(f"🎮 Creating match {match_id} for {player1} vs {player2}")
        
        game = EscobaGame(match_id, player1, player2)
        
        if not save_match(game):
            return jsonify({"error": "Failed to save match"}), 500

        print(f"✅ Match created: {match_id}")

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
            return jsonify({"error": "Player not in this match"}), 403

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
            
            # If game finished, save to history
            if game.status == "finished":
                save_match_to_history(game)
                
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
    """Delete a match"""
    try:
        if delete_match(match_id):
            return jsonify({"message": "Match deleted successfully"})
        else:
            return jsonify({"error": "Failed to delete match"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to delete match: {str(e)}"}), 500

@app.route('/match', methods=['GET'])
def list_matches():
    """List all active matches"""
    try:
        if redis_client is None:
            return jsonify({"error": "Redis not available"}), 503
            
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
                    "current_player": match_obj["players"][match_obj["current_player_index"]]
                })
        
        return jsonify({
            "active_matches": len(matches),
            "matches": matches
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list matches: {str(e)}"}), 500

if __name__ == '__main__':
    print("🎮 Match Service starting on port 5003...")
    print("⏳ Waiting for Redis connection...")
    
    try:
        redis_client = get_redis_client()
        print("🃏 La Escoba game logic loaded")
        print("🗄️ Redis storage enabled")
        print("✅ Match service ready")
    except Exception as e:
        print(f"⚠️ Warning: Redis not available: {e}")
        print("⚠️ Service will run but matches cannot be saved")
    
    app.run(host='0.0.0.0', port=5003, debug=False)
