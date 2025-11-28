from flask import Flask, request, jsonify
import random
import uuid
from datetime import datetime
import redis
import requests
import json
from flask_cors import CORS  # AGGIUNGI

app = Flask(__name__)
CORS(app)  # AGGIUNGI

# Configurazione Redis
redis_client = redis.Redis(host='match-db', port=6379, db=0, decode_responses=True)

class EscobaGame:
    """Logica completa del gioco La Escoba"""

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
        
        # Inizializza partita
        self._initialize_game()

    def _initialize_game(self):
        """Inizializza una nuova partita"""
        # Crea mazzo (40 carte spagnole)
        self.deck = list(range(1, 41))
        random.shuffle(self.deck)
        
        # Distribuisci 3 carte a ogni giocatore
        for player in self.players:
            self.player_hands[player] = [self.deck.pop() for _ in range(3)]
        
        # Metti 4 carte sul tavolo
        self.table_cards = [self.deck.pop() for _ in range(4)]

    def _get_card_value(self, card_id):
        """Restituisce il valore della carta per il gioco (1-10)"""
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
        """Restituisce il seme della carta"""
        if 1 <= card_id <= 10:
            return "Oros"
        elif 11 <= card_id <= 20:
            return "Copas" 
        elif 21 <= card_id <= 30:
            return "Espadas"
        else:
            return "Bastos"

    def _find_card_combinations(self, target_sum, available_cards):
        """Trova tutte le combinazioni di carte che sommano a target_sum"""
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
        """Gioca una carta"""
        if player != self.current_player:
            return False, "Non è il tuo turno"
        
        if card_id not in self.player_hands[player]:
            return False, "Carta non nella tua mano"
        
        # Trova tutte le possibili catture
        played_card_value = self._get_card_value(card_id)
        target_sum = 15 - played_card_value
        possible_captures = self._find_card_combinations(target_sum, self.table_cards)
        
        # Se non ci sono catture possibili, la carta va sul tavolo
        if not possible_captures:
            self.table_cards.append(card_id)
            self.player_hands[player].remove(card_id)
            move_result = "carta_aggiunta_al_tavolo"
            captured_cards = []
        else:
            # Prendi la prima combinazione valida (per semplicità)
            captured_cards = possible_captures[0]
            # Rimuovi carte catturate dal tavolo
            for card in captured_cards:
                self.table_cards.remove(card)
            # Aggiungi alla collezione del giocatore
            self.captured_cards[player].extend(captured_cards)
            self.captured_cards[player].append(card_id)  # Anche la carta giocata
            self.player_hands[player].remove(card_id)
            move_result = "carte_catturate"
            
            # Controlla se è una scopa (tavolo vuoto)
            if len(self.table_cards) == 0:
                self.scores[player] += 1  # Punto scopa
                move_result = "scopa"

        # Registra mossa
        move = {
            "player": player,
            "card_played": card_id,
            "captured_cards": captured_cards,
            "result": move_result,
            "timestamp": datetime.now().isoformat()
        }
        self.moves.append(move)
        
        # Cambia turno
        self.current_player = self.players[1] if player == self.players[0] else self.players[0]
        
        # Pesca nuova carta se il mazzo non è vuoto
        if self.deck and len(self.player_hands[player]) < 3:
            new_card = self.deck.pop()
            self.player_hands[player].append(new_card)
        
        # Controlla se la partita è finita
        if self._is_game_over():
            self._end_game()
        
        return True, move_result

    def _is_game_over(self):
        """Controlla se la partita è finita"""
        # Partita finisce quando non ci sono più carte nel mazzo e i giocatori hanno finito le carte
        return len(self.deck) == 0 and all(len(hand) == 0 for hand in self.player_hands.values())

    def _end_game(self):
        """Calcola punteggio finale e termina partita"""
        self.status = "finished"
        
        # Calcola punteggi finali
        final_scores = self._calculate_final_scores()
        self.scores = final_scores
        
        # Determina vincitore
        if self.scores[self.players[0]] > self.scores[self.players[1]]:
            winner = self.players[0]
        elif self.scores[self.players[1]] > self.scores[self.players[0]]:
            winner = self.players[1]
        else:
            winner = "draw"
        
        # Salva in History Service
        self._save_to_history(winner)
        
        # Aggiorna statistiche giocatori
        self._update_player_stats(winner)

    def _calculate_final_scores(self):
        """Calcola punteggi finali secondo regole La Escoba"""
        scores = {self.players[0]: 0, self.players[1]: 0}
        
        for player in self.players:
            captured = self.captured_cards[player]
            
            # 1. Scope (già conteggiate durante il gioco)
            scores[player] += self.scores[player]
            
            # 2. Sette di Oros e Copas
            for card_id in captured:
                if card_id == 7:  # 7 di Oros
                    scores[player] += 1
                elif card_id == 17:  # 7 di Copas
                    scores[player] += 1
            
            # 3. Maggior numero di carte
            if len(captured) > len(self.captured_cards[self._get_opponent(player)]):
                scores[player] += 1
            
            # 4. Maggior numero di Oros
            player_oros = len([c for c in captured if self._get_card_suit(c) == "Oros"])
            opponent_oros = len([c for c in self.captured_cards[self._get_opponent(player)] 
                               if self._get_card_suit(c) == "Oros"])
            if player_oros > opponent_oros:
                scores[player] += 1
        
        return scores

    def _get_opponent(self, player):
        """Restituisce l'avversario"""
        return self.players[1] if player == self.players[0] else self.players[0]

    def _save_to_history(self, winner):
        """Salva partita in History Service"""
        try:
            match_data = {
                "match_id": self.match_id,
                "player1": self.players[0],
                "player2": self.players[1],
                "winner": winner,
                "scores": self.scores,
                "moves": self.moves,
                "end_time": datetime.now().isoformat()
            }
            requests.post(
                "http://history-service:5005/history/matches",
                json=match_data,
                timeout=5
            )
        except Exception as e:
            print(f"Errore salvataggio history: {e}")

    def _update_player_stats(self, winner):
        """Aggiorna statistiche giocatori"""
        try:
            for player in self.players:
                result = "win" if player == winner else "loss" if winner != "draw" else "draw"
                score_delta = self.scores[player]
                
                requests.put(
                    f"http://player-service:5004/players/{player}/stats",
                    json={
                        "match_result": result,
                        "score_delta": score_delta
                    },
                    timeout=5
                )
        except Exception as e:
            print(f"Errore aggiornamento stats: {e}")

    def get_game_state(self, player):
        """Restituisce stato partita per un giocatore"""
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
            "message": f"Stato partita per {player}"
        }

    def to_dict(self):
        """Converte oggetto in dict per Redis"""
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
            "deck": self.deck
        }

    @classmethod
    def from_dict(cls, data):
        """Crea oggetto da dict"""
        game = cls(data["match_id"], data["players"][0], data["players"][1])
        game.current_player = data["current_player"]
        game.status = data["status"]
        game.table_cards = data["table_cards"]
        game.player_hands = data["player_hands"]
        game.scores = data["scores"]
        game.captured_cards = data["captured_cards"]
        game.moves = data["moves"]
        game.deck = data["deck"]
        return game

# Storage partite (Redis)
def save_match(game):
    """Salva partita in Redis"""
    redis_client.set(f"match:{game.match_id}", json.dumps(game.to_dict()))

def load_match(match_id):
    """Carica partita da Redis"""
    data = redis_client.get(f"match:{match_id}")
    if data:
        return EscobaGame.from_dict(json.loads(data))
    return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Matches service is running"})

@app.route('/matches', methods=['POST'])
def create_match():
    """Crea nuova partita"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    player1 = data.get('player1')
    player2 = data.get('player2')

    if not player1 or not player2:
        return jsonify({"error": "Entrambi i giocatori richiesti"}), 400

    match_id = str(uuid.uuid4())
    game = EscobaGame(match_id, player1, player2)
    save_match(game)

    return jsonify({
        "match_id": match_id,
        "players": [player1, player2],
        "message": "Partita creata con successo",
        "initial_table": game.table_cards
    }), 201

@app.route('/matches/<match_id>', methods=['GET'])
def get_match(match_id):
    """Ottieni stato partita"""
    game = load_match(match_id)
    if not game:
        return jsonify({"error": "Partita non trovata"}), 404

    player = request.args.get('player')
    if not player:
        return jsonify({"error": "Parametro player richiesto"}), 400

    if player not in game.players:
        return jsonify({"error": "Giocatore non partecipa a questa partita"}), 403

    return jsonify(game.get_game_state(player))

@app.route('/matches/<match_id>/play', methods=['POST'])
def play_card(match_id):
    """Gioca una carta"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400

    player = data.get('player')
    card_id = data.get('card_id')

    if not player or not card_id:
        return jsonify({"error": "Player e card_id richiesti"}), 400

    game = load_match(match_id)
    if not game:
        return jsonify({"error": "Partita non trovata"}), 404

    success, message = game.play_card(player, card_id)
    
    if success:
        save_match(game)  # Salva stato aggiornato
        return jsonify({
            "message": message,
            "game_state": game.get_game_state(player)
        })
    else:
        return jsonify({"error": message}), 400

if __name__ == '__main__':
    print("🎮 Match Service starting on port 5003...")
    print("🃏 La Escoba game logic loaded")
    print("🗄️  Redis storage enabled")
    app.run(host='0.0.0.0', port=5003, debug=True)

