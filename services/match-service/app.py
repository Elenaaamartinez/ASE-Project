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
        self._deal_cards()
    
    def _deal_cards(self):
        """Deal initial cards to players and table"""
        deck = list(range(1, 41))
        random.shuffle(deck)
        for player in self.players:
            self.player_hands[player] = [deck.pop() for _ in range(3)]
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
            "scores": self.scores
        }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Matches service is running"})

@app.route('/matches', methods=['POST'])
def create_match():
    data = request.get_json()
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
    game = matches_db.get(match_id)
    if not game:
        return jsonify({"error": "Match not found"}), 404
    
    player = request.args.get('player')
    if not player:
        return jsonify({"error": "Player parameter required"}), 400
    
    return jsonify(game.get_game_state(player))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)

