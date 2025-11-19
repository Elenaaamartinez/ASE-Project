from flask import Flask, request, jsonify
import random
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage for matches
matches_db = {}
players_db = {}

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
    
    def play_card(self, player, card_id, target_card_ids=None):
        """Play a card from player's hand"""
        if player != self.current_player:
            return False, "Not your turn"
        
        if card_id not in self.player_hands[player]:
            return False, "Card not in hand"
        
        # Simple capture logic for demo
        # In real Escoba, you can capture cards that sum to the played card's value
        card_value = self._get_card_value(card_id)
        captured_cards = []
        
        # Check if any single card can be captured
        for table_card in self.table_cards[:]:
            table_value = self._get_card_value(table_card)
            if table_value == card_value:
                captured_cards.append(table_card)
                self.table_cards.remove(table_card)
                break
        
        # Remove played card from hand
        self.player_hands[player].remove(card_id)
        captured_cards.append(card_id)
        self.captured[player].extend(captured_cards)
        
        # Record move
        move = {
            "player": player,
            "card_played": card_id,
            "cards_captured": captured_cards,
            "timestamp": datetime.now().isoformat()
        }
        self.moves.append(move)
        
        # Check for escoba (sweep)
        if len(self.table_cards) == 0:
            self.scores[player] += 1  # Escoba point
        
        # Switch player
        self.current_player = self.players[1] if player == self.players[0] else self.players[0]
        
        # Check if round is over (all cards played)
        if all(len(hand) == 0 for hand in self.player_hands.values()):
            self._calculate_round_score()
            # For demo, end game after one round
            self.status = "finished"
        
        return True, "Card played successfully"
    
    def _get_card_value(self, card_id):
        """Get card value for game logic (1-7 have face value, 8-10 are worth 10)"""
        if 1 <= card_id <= 7:
            return card_id % 10  # 1-7
        else:
            return 10  # Sota, Caballo, Rey
    
    def _calculate_round_score(self):
        """Calculate scores at the end of round (simplified)"""
        # Count cards captured
        cards_p1 = len(self.captured[self.players[0]])
        cards_p2 = len(self.captured[self.players[1]])
        
        if cards_p1 > cards_p2:
            self.scores[self.players[0]] += 1
        elif cards_p2 > cards_p1:
            self.scores[self.players[1]] += 1
        
        # Count coins (Oros) captured
        oros_p1 = sum(1 for card in self.captured[self.players[0]] if 1 <= card <= 10)
        oros_p2 = sum(1 for card in self.captured[self.players[1]] if 1 <= card <= 10)
        
        if oros_p1 > oros_p2:
            self.scores[self.players[0]] += 1
        elif oros_p2 > oros_p1:
            self.scores[self.players[1]] += 1
    
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
            "your_captured": self.captured.get(player, []),
            "moves": self.moves[-5:]  # Last 5 moves
        }

@app.route('/matches', methods=['POST'])
def create_match():
    """Create a new match"""
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
    """Get match state"""
    game = matches_db.get(match_id)
    
    if not game:
        return jsonify({"error": "Match not found"}), 404
    
    player = request.args.get('player')
    if not player:
        return jsonify({"error": "Player parameter required"}), 400
    
    return jsonify(game.get_game_state(player))

@app.route('/matches/<match_id>', methods=['GET'])
def get_match(match_id):
    """Get match state"""
    game = matches_db.get(match_id)
    
    if not game:
        return jsonify({"error": "Match not found"}), 404
    
    # Get player from query parameters (not JSON body)
    player = request.args.get('player')
    if not player:
        return jsonify({"error": "Player parameter required"}), 400
    
    return jsonify(game.get_game_state(player))
    
    game = matches_db.get(match_id)
    if not game:
        return jsonify({"error": "Match not found"}), 404
    
    success, message = game.play_card(player, card_id, target_cards)
    
    if success:
        return jsonify({
            "message": message,
            "game_state": game.get_game_state(player)
        })
    else:
        return jsonify({"error": message}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "Matches service is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)

