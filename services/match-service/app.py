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

redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'match-db'), 
    port=int(os.environ.get('REDIS_PORT', 6379)), 
    db=0, 
    decode_responses=True
)

HISTORY_SERVICE_URL = os.environ.get('HISTORY_SERVICE_URL', 'http://history-service:5005')

# --- LOGICA DI GIOCO ---
class EscobaGame:
    def __init__(self, match_id, player1, player2):
        self.match_id = match_id
        self.players = [player1, player2]
        self.current_player = player1
        self.deck = list(range(1, 41))
        random.shuffle(self.deck)
        self.table_cards = []
        self.hands = {player1: [], player2: []}
        self.captured = {player1: [], player2: []}
        self.scores = {player1: 0, player2: 0}
        self.status = "active"
        self.moves_log = []
        
        # Distribuzione iniziale
        for _ in range(3):
            self.hands[player1].append(self.deck.pop())
            self.hands[player2].append(self.deck.pop())
        for _ in range(4):
            self.table_cards.append(self.deck.pop())

    def to_dict(self):
        return self.__dict__
    
    @staticmethod
    def from_dict(data):
        game = EscobaGame(data["match_id"], data["players"][0], data["players"][1])
        game.__dict__.update(data)
        return game

    def get_game_state(self, player):
        return {
            "match_id": self.match_id,
            "players": self.players,
            "current_player": self.current_player,
            "your_hand": self.hands.get(player, []),
            "table_cards": self.table_cards,
            "scores": self.scores,
            "status": self.status,
            "captured_cards": self.captured.get(player, [])
        }

    def play_card(self, player, card_id):
        if self.status != "active" or player != self.current_player:
            return False, "Invalid move"
        
        if card_id not in self.hands[player]:
            return False, "Card not in hand"
        
        # Logica base: gioca carta sul tavolo (semplificata per ora)
        self.hands[player].remove(card_id)
        self.table_cards.append(card_id)
        
        # Cambio turno
        self.current_player = self.players[1] if player == self.players[0] else self.players[0]
        
        # Controllo fine mano/partita
        if not self.hands[self.players[0]] and not self.hands[self.players[1]]:
            if self.deck:
                for _ in range(3):
                    for p in self.players:
                        self.hands[p].append(self.deck.pop())
            else:
                self.status = "finished"
                self.scores = {p: random.randint(1,10) for p in self.players} # Punteggio simulato
        
        return True, "Card played"

def send_match_to_history(game):
    try:
        winner = max(game.scores, key=game.scores.get) if game.scores[game.players[0]] != game.scores[game.players[1]] else "draw"
        payload = {
            "match_id": game.match_id,
            "player1": game.players[0],
            "player2": game.players[1],
            "winner": winner,
            "scores": game.scores,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "moves": game.moves_log
        }
        requests.post(f"{HISTORY_SERVICE_URL}/history/matches", json=payload)
        print(f"✅ Match {game.match_id} sent to history")
    except Exception as e:
        print(f"❌ History sync failed: {e}")

# --- ENDPOINTS ---

@app.route('/match', methods=['POST'])
def create_match():
    data = request.json
    match_id = str(uuid.uuid4())
    game = EscobaGame(match_id, data['player1'], data['player2'])
    redis_client.set(f"match:{match_id}", json.dumps(game.to_dict()))
    return jsonify({"match_id": match_id, "status": "active"}), 201

@app.route('/match/<match_id>', methods=['GET'])
def get_match(match_id):
    data = redis_client.get(f"match:{match_id}")
    if not data: return jsonify({"error": "Not found"}), 404
    game = EscobaGame.from_dict(json.loads(data))
    return jsonify(game.get_game_state(request.args.get('player')))

@app.route('/match/<match_id>/play', methods=['POST'])
def play_card(match_id):
    data = redis_client.get(f"match:{match_id}")
    if not data: return jsonify({"error": "Not found"}), 404
    
    game = EscobaGame.from_dict(json.loads(data))
    success, msg = game.play_card(request.json['player'], int(request.json['card_id']))
    
    if success:
        if game.status == "finished":
            send_match_to_history(game) # INTEGRAZIONE CRITICA QUI
        redis_client.set(f"match:{match_id}", json.dumps(game.to_dict()))
        return jsonify({"message": msg, "game_state": game.get_game_state(request.json['player'])})
    return jsonify({"error": msg}), 400

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "Match service running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
