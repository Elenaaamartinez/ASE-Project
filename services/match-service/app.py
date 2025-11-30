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

    def __init__(self, match_id, player1, player2):
        self.match_id = match_id
        self.players = [player1, player2]
        self.current_player = player1
        self.status = "active"  # active, finished
        self.table_cards = []
        self.player_hands = {player1: [], player2: []}
        self.scores = {player1: 0, player2: 0}
        self.captured_cards = {player1: [], player2: []}
        self.moves = []
        self.deck = []
        self.created_at = datetime.now().isoformat()
        
        # Initialize game
        self._initialize_game()

    def _initialize_game(self):
        """Initialize a new game"""
        # Create deck (40 Spanish cards)
        self.deck = list(range(1, 41))
        random.shuffle(self.deck)
        
        # Deal 3 cards to each player
        for player in self.players:
            self.player_hands[player] = [self.deck.pop() for _ in range(3)]
        
        # Put 4 cards on the table
        self.table_cards = [self.deck.pop() for _ in range(4)]

    def _get_card_value(self, card_id):
        """Return card value for game (1-10)"""
        if 1 <= card_id <= 7:
            return card_id
        elif 8 <= card_id <= 10:  # Sota de Oros, Copas, Espadas
            return 8
        elif 11 <= card_id <= 13:  # Caballo de Oros, Copas, Espadas  
            return 9
        elif 14 <= card_id <= 16:  # Rey de Oros, Copas, Espadas
            return 10
        elif 17 <= card_id <= 23:  # 1-7 de Bastos
            return card_id - 16
        elif 24 <= card_id <= 26:  # Sota de Bastos
            return 8
        elif 27 <= card_id <= 29:  # Caballo de Bastos
            return 9
        else:  # 30-40: Rey de Bastos e resto
            return 10

    def _get_card_suit(self, card_id):
        """Return card suit"""
        if 1 <= card_id <= 10:
            return "Oros"
        elif 11 <= card_id <= 20:
            return "Copas" 
        elif 21 <= card_id <= 30:
            return "Espadas"
        else:
            return "Bastos"

    def _find_card_combinations(self, target_sum, available_cards):
        """Find all card combinations that sum to target_sum"""
        def find_combinations(start, current_sum, current_combo):
            if current_sum == target_sum:
                results.append(current_combo[:])
                return
            if current_sum > target_sum or start >= len(available_cards):
                return
            
            for i in range(start, len(available_cards)):
                card_id = available_cards[i]
                card_value = self._get_card_value(card_id)
                current_combo.append(card_id)
                find_combinations(i + 1, current_sum + card_value, current_combo)
                current_combo.pop()
        
        results = []
        find_combinations(0, 0, [])
        return results

    def play_card(self, player, card_id):
        """Play a card"""
        if player != self.current_player:
            return False, "Not your turn"
        
        if card_id not in self.player_hands[player]:
            return False, "Card not in your hand"
        
        # Find all possible captures
        played_card_value = self._get_card_value(card_id)
        target_sum = 15 - played_card_value
        possible_captures = self._find_card_combinations(target_sum, self.table_cards)
        
        # If no captures possible, card goes to table
        if not possible_captures:
            self.table_cards.append(card_id)
            self.player_hands[player].remove(card_id)
            move_result = "card_added_to_table"
            captured_cards = []
        else:
            # Take first valid combination (for simplicity)
            captured_cards = possible_captures[0]
            # Remove captured cards from table
            for card in captured_cards:
                self.table_cards.remove(card)
            # Add to player collection
            self.captured_cards[player].extend(captured_cards)
            self.captured_cards[player].append(card_id)  # Also the played card
            self.player_hands[player].remove(card_id)
            move_result = "cards_captured"
            
            # Check if it's a scopa (empty table)
            if len(self.table_cards) == 0:
                self.scores[player] += 1  # Scopa point
                move_result = "scopa"

        # Record move
        move = {
            "player": player,
            "card_played": card_id,
            "captured_cards": captured_cards,
            "result": move_result,
            "timestamp": datetime.now().isoformat()
        }
        self.moves.append(move)
        
        # Change turn
        self.current_player = self.players[1] if player == self.players[0] else self.players[0]
        
        # Draw new card if deck not empty
        if self.deck and len(self.player_hands[player]) < 3:
            new_card = self.deck.pop()
            self.player_hands[player].append(new_card)
        
        # Check if game is over
        if self._is_game_over():
            self._end_game()
        
        return True, move_result

    def _is_game_over(self):
        """Check if game is over"""
        # Game ends when no more cards in deck and players have no cards
        return len(self.deck) == 0 and all(len(hand) == 0 for hand in self.player_hands.values())

    def _end_game(self):
        """Calculate final score and end game"""
        self.status = "finished"
        
        # Calculate final scores
        final_scores = self._calculate_final_scores()
        self.scores = final_scores
        
        # Determine winner
        if self.scores[self.players[0]] > self.scores[self.players[1]]:
            winner = self.players[0]
        elif self.scores[self.players[1]] > self.scores[self.players[0]]:
            winner = self.players[1]
        else:
            winner = "draw"
        
        # Save to History Service
        self._save_to_history(winner)
        
        # Update player statistics
        self._update_player_stats(winner)

    def _calculate_final_scores(self):
        """Calculate final scores according to La Escoba rules"""
        scores = {self.players[0]: 0, self.players[1]: 0}
        
        for player in self.players:
            captured = self.captured_cards[player]
            
            # 1. Scopas (already counted during game)
            scores[player] += self.scores[player]
            
            # 2. Seven of Oros and Copas
            for card_id in captured:
                if card_id == 7:  # 7 of Oros
                    scores[player] += 1
                elif card_id == 17:  # 7 of Copas
                    scores[player] += 1
            
            # 3. Most cards
            if len(captured) > len(self.captured_cards[self._get_opponent(player)]):
                scores[player] += 1
            
            # 4. Most Oros
            player_oros = len([c for c in captured if self._get_card_suit(c) == "Oros"])
            opponent_oros = len([c for c in self.captured_cards[self._get_opponent(player)] 
                               if self._get_card_suit(c) == "Oros"])
            if player_oros > opponent_oros:
                scores[player] += 1
        
        return scores

    def _get_opponent(self, player):
        """Return opponent"""
        return self.players[1] if player == self.players[0] else self.players[0]

    def _save_to_history(self, winner):
        """Save match to History Service"""
        try:
            match_data = {
                "match_id": self.match_id,
                "player1": self.players[0],
                "player2": self.players[1],
                "winner": winner,
                "scores": self.scores,
                "moves": self.moves,
                "start_time": self.created_at,
                "end_time": datetime.now().isoformat()
            }
            
            response = requests.post(
                "http://history-service:5005/history/matches",
                json=match_data,
                timeout=10
            )
            
            if response.status_code == 201:
                print(f"✅ Match {self.match_id} saved to history")
            else:
                print(f"❌ Failed to save match to history: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error saving to history: {e}")

    def _update_player_stats(self, winner):
        """Update player statistics"""
        try:
            for player in self.players:
                result = "win" if player == winner else "loss" if winner != "draw" else "draw"
                score_delta = self.scores[player]
                
                response = requests.put(
                    f"http://player-service:5004/players/{player}/stats",
                    json={
                        "match_result": result,
                        "score_delta": score_delta
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Updated stats for {player}")
                else:
                    print(f"❌ Failed to update stats for {player}: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error updating stats: {e}")

    def get_game_state(self, player):
        """Return game state for a player"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.current_player,
            "status": self.status,
            "table_cards": self.table_cards,
            "your_hand": self.player_hands.get(player, []),
            "scores": self.scores,
            "captured_cards": self.captured_cards.get(player, []),
            "remaining_deck": len(self.deck),
            "moves_count": len(self.moves),
            "message": f"Game state for {player}"
        }

    def to_dict(self):
        """Convert object to dict for Redis"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.current_player,
            "status": self.status,
            "table_cards": self.table_cards,
            "player_hands": self.player_hands,
            "scores": self.scores,
            "captured_cards": self.captured_cards,
            "moves": self.moves,
            "deck": self.deck,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Create object from dict"""
        game = cls(data["match_id"], data["players"][0], data["players"][1])
        game.current_player = data["current_player"]
        game.status = data["status"]
        game.table_cards = data["table_cards"]
        game.player_hands = data["player_hands"]
        game.scores = data["scores"]
        game.captured_cards = data["captured_cards"]
        game.moves = data["moves"]
        game.deck = data["deck"]
        game.created_at = data.get("created_at", datetime.now().isoformat())
        return game

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
            "status": "Matches service is running",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "Matches service is running",
            "redis": "disconnected",
            "error": str(e)
        }), 503

@app.route('/matches', methods=['POST'])
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

@app.route('/matches/<match_id>', methods=['GET'])
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

@app.route('/matches/<match_id>/play', methods=['POST'])
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

@app.route('/matches/<match_id>', methods=['DELETE'])
def delete_match_endpoint(match_id):
    """Delete a match (admin only)"""
    try:
        if delete_match(match_id):
            return jsonify({"message": "Match deleted successfully"})
        else:
            return jsonify({"error": "Failed to delete match"}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to delete match: {str(e)}"}), 500

@app.route('/matches', methods=['GET'])
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
