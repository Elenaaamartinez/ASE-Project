from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'history-db'),
        database=os.environ.get('DB_NAME', 'history_db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )
    return conn

def init_db():
    """Inizializza database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tabella partite
    cur.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(100) UNIQUE NOT NULL,
            player1 VARCHAR(50) NOT NULL,
            player2 VARCHAR(50) NOT NULL,
            winner VARCHAR(50),
            scores JSONB,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status VARCHAR(20) DEFAULT 'completed'
        )
    ''')
    
    # Tabella mosse
    cur.execute('''
        CREATE TABLE IF NOT EXISTS match_moves (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(100) NOT NULL,
            player VARCHAR(50) NOT NULL,
            card_played INTEGER,
            captured_cards JSONB,
            move_result VARCHAR(50),
            move_timestamp TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches(match_id)
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ History database initialized")

@app.route('/history/<username>', methods=['GET'])
def get_player_history(username):
    """Ottieni storico partite di un giocatore"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT match_id, player1, player2, winner, scores, start_time, end_time
        FROM matches 
        WHERE player1 = %s OR player2 = %s
        ORDER BY end_time DESC
    ''', (username, username))
    
    matches = []
    for row in cur.fetchall():
        match_id, player1, player2, winner, scores, start_time, end_time = row
        
        # Determina risultato per il giocatore richiesto
        if winner == username:
            result = "win"
        elif winner == "draw":
            result = "draw"
        else:
            result = "loss"
        
        matches.append({
            "match_id": match_id,
            "player1": player1,
            "player2": player2,
            "winner": winner,
            "your_result": result,
            "scores": scores,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        "username": username,
        "match_count": len(matches),
        "matches": matches
    })

@app.route('/history/matches', methods=['POST'])
def save_match_result():
    """Salva risultato partita"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "JSON data required"}), 400
        
    required_fields = ['match_id', 'player1', 'player2', 'winner', 'scores']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo mancante: {field}"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Inserisci partita
        cur.execute('''
            INSERT INTO matches (match_id, player1, player2, winner, scores, end_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data['match_id'],
            data['player1'],
            data['player2'],
            data['winner'],
            json.dumps(data['scores']),
            datetime.now()
        ))
        
        # Inserisci mosse se presenti
        moves = data.get('moves', [])
        for move in moves:
            cur.execute('''
                INSERT INTO match_moves (match_id, player, card_played, captured_cards, move_result, move_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                data['match_id'],
                move['player'],
                move['card_played'],
                json.dumps(move['captured_cards']),
                move['result'],
                move.get('timestamp')
            ))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Errore salvataggio: {str(e)}"}), 500
        
    finally:
        cur.close()
        conn.close()
    
    return jsonify({"message": "Partita salvata nello storico"}), 201

@app.route('/history/matches/<match_id>', methods=['GET'])
def get_match_details(match_id):
    """Ottieni dettagli completi di una partita"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Dati partita
    cur.execute('''
        SELECT player1, player2, winner, scores, start_time, end_time
        FROM matches WHERE match_id = %s
    ''', (match_id,))
    
    match_data = cur.fetchone()
    if not match_data:
        return jsonify({"error": "Partita non trovata"}), 404
    
    player1, player2, winner, scores, start_time, end_time = match_data
    
    # Mosse della partita
    cur.execute('''
        SELECT player, card_played, captured_cards, move_result, move_timestamp
        FROM match_moves 
        WHERE match_id = %s
        ORDER BY move_timestamp
    ''', (match_id,))
    
    moves = []
    for move_row in cur.fetchall():
        player, card_played, captured_cards, move_result, move_timestamp = move_row
        moves.append({
            "player": player,
            "card_played": card_played,
            "captured_cards": captured_cards,
            "result": move_result,
            "timestamp": move_timestamp.isoformat() if move_timestamp else None
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        "match_id": match_id,
        "player1": player1,
        "player2": player2,
        "winner": winner,
        "scores": scores,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "moves": moves
    })

@app.route('/health', methods=['GET'])
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            "status": "History service is running", 
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "History service is running", 
            "database": "disconnected",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    print("📊 Initializing History Service database...")
    init_db()
    print("✅ History service starting on port 5005...")
    app.run(host='0.0.0.0', port=5005, debug=True)
