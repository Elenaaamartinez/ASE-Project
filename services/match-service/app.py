from flask import Flask, request, jsonify
import random
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage for matches
matches_db = {}

class EscobaGame:
    """Simple Escoba game logic"""

    def __init__(self, match_id, player1, player2):
        self.match_id = match_id
        self.players = [player1, player2]
        self.current_player = player1
        self.status = "active"
        self.table_cards = []
        self.player_hands = {player1: [], player2: []}
        self.scores = {player1: 0, player2: 0}
        self.captured = {player1: [], player2: []}
        self.moves = []

        # Initialize game
        self._deal_cards()

    def _deal_cards(self):
        """Deal initial cards to players and table"""
        # Create a deck (simplified - using card IDs 1-40)
        deck = list(range(1, 41))
        random.shuffle(deck)

        # Deal 3 cards to each player
        for player in self.players:
            self.player_hands[player] = [deck.pop() for _ in range(3)]

        # Deal 4 cards to table
        self.table_cards = [deck.pop() for _ in range(4)]

    def _get_card_value(self, card_id):
        """Get card value for game logic"""
        if 1 <= card_id <= 7:
            return card_id % 10
        else:
            return 10

    def get_game_state(self, player):
        """Get game state for a specific player"""
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.current_player,
            "status": self.status,
            "table_cards": self.table_cards,
            "your_hand": self.player_hands.get(player, []),
            "scores": self.scores,
            "message": f"Game state for {player}"
        }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Matches service is running"})

@app.route('/matches', methods=['POST'])
def create_match():
    """Create a new match - REQUIRES Content-Type: application/json"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    player1 = data.get('player1')
    player2 = data.get('player2')

    if not player1 or not player2:
        return jsonify({"error": "Both players required"}), 400

    match_id = str(uuid.uuid4())
    game = EscobaGame(match_id, player1, player2)
    matches_db[match_id] = game

    return jsonify({
        "match_id": match_id,
        "players": [player1, player2],
        "message": "Match created successfully"
    }), 201

@app.route('/matches/<match_id>', methods=['GET'])
def get_match(match_id):
    """Get match state - DOES NOT require Content-Type"""
    game = matches_db.get(match_id)

    if not game:
        return jsonify({"error": "Match not found"}), 404

    # CORRETTO: per GET usa request.args, non JSON!
    player = request.args.get('player')
    if not player:
        return jsonify({"error": "Player parameter required"}), 400

    return jsonify(game.get_game_state(player))

@app.route('/matches/<match_id>/play', methods=['POST'])
def play_card(match_id):
    """Play a card - REQUIRES Content-Type: application/json"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    player = data.get('player')
    card_id = data.get('card_id')

    if not player or not card_id:
        return jsonify({"error": "Player and card_id required"}), 400

    game = matches_db.get(match_id)
    if not game:
        return jsonify({"error": "Match not found"}), 404

    # Simple game logic
    if player != game.current_player:
        return jsonify({"error": "Not your turn"}), 400

    if card_id not in game.player_hands[player]:
        return jsonify({"error": "Card not in hand"}), 400

    # Remove card from hand
    game.player_hands[player].remove(card_id)

    # Switch player
    game.current_player = game.players[1] if player == game.players[0] else game.players[0]

    return jsonify({
        "message": f"Player {player} played card {card_id}",
        "game_state": game.get_game_state(player)
    })

if __name__ == '__main__':
    print("✔ Matches service starting on port 5003...")
    app.run(host='0.0.0.0', port=5003, debug=True)
