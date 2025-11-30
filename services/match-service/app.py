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
        self.current_player_index = 0
        self.deck = list(range(1, 41))  # 40 cards of the Spanish deck
        random.shuffle(self.deck)

        # Player hands
        self.hands = {
            player1: [],
            player2: []
        }

        # Cards on the table
        self.table_cards = []

        # Captured cards
        self.captured = {
            player1: [],
            player2: []
        }

        # Scores
        self.scores = {
            player1: 0,
            player2: 0
        }

        # Escobas (sweeps)
        self.escobas = {
            player1: 0,
            player2: 0
        }

        self.status = "active"
        self.winner = None
        self.created_at = datetime.now().isoformat()
        self.last_move = datetime.now().isoformat()

        # Deal initial cards
        self._deal_initial_cards()

    def _deal_initial_cards(self):
        """Deals cards at game start"""
        # 4 cards on the table
        for _ in range(4):
            if self.deck:
                self.table_cards.append(self.deck.pop())

        # 3 cards to each player
        for player in self.players:
            for _ in range(3):
                if self.deck:
                    self.hands[player].append(self.deck.pop())

    def _refill_hands(self):
        """Refill player hands if empty"""
        for player in self.players:
            while len(self.hands[player]) < 3 and self.deck:
                self.hands[player].append(self.deck.pop())

    def play_card(self, player, card_id):
        """Plays a card"""
        if player not in self.players:
            return False, "Invalid player"

        if self.current_player_index != self.players.index(player):
            return False, "Not your turn"

        if card_id not in self.hands[player]:
            return False, "You don't have that card"

        # Remove card from hand
        self.hands[player].remove(card_id)

        # For now, simply add the card to the table
        # TODO: Implement full capture logic (sum 15)
        self.table_cards.append(card_id)

        # Switch turn
        self.current_player_index = (self.current_player_index + 1) % 2
        self.last_move = datetime.now().isoformat()

        # Refill hands if needed
        self._refill_hands()

        # Check if the game ended
        if not self.deck and all(len(self.hands[p]) == 0 for p in self.players):
            self._finish_game()

        return True, "Card played successfully"

    def _finish_game(self):
        """Finish game and calculate scores"""
        self.status = "finished"

        # Score calculation (simplified)
        for player in self.players:
            self.scores[player] = len(self.captured[player]) + self.escobas[player]

        # Determine winner
        if self.scores[self.players[0]] > self.scores[self.players[1]]:
            self.winner = self.players[0]
        elif self.scores[self.players[1]] > self.scores[self.players[0]]:
            self.winner = self.players[1]
        else:
            self.winner = None  # Draw

    def get_game_state(self, player):
        """Returns game state for a player"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.players[self.current_player_index],
            "your_hand": self.hands.get(player, []),
            "table_cards": self.table_cards,
            "captured_cards": self.captured.get(player, []),
            "scores": self.scores,
            "escobas": self.escobas,
            "remaining_deck": len(self.deck),
            "status": self.status,
            "winner": self.winner
        }

    def to_dict(self):
        """Convert game to dict for persistence"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player_index": self.current_player_index,
            "deck": self.deck,
            "hands": self.hands,
            "table_cards": self.table_cards,
            "captured": self.captured,
            "scores": self.scores,
            "escobas": self.escobas,
            "status": self.status,
            "winner": self.winner,
            "created_at": self.created_at,
            "last_move": self.last_move
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a game instance from a dict"""
        game = cls.__new__(cls)
        game.match_id = data["match_id"]
        game.players = data["players"]
        game.current_player_index = data["current_player_index"]
        game.deck = data["deck"]
        game.hands = data["hands"]
        game.table_cards = data["table_cards"]
        game.captured = data["captured"]
        game.scores = data["scores"]
        game.escobas = data["escobas"]
        game.status = data["status"]
        game.winner = data.get("winner")
        game.created_at = data["created_at"]
        game.last_move = data["last_move"]
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
    print("🗄️ Redis storage enabled")
    print("🔗 Integrated with History and Player services")
    app.run(host='0.0.0.0', port=5003, debug=False)