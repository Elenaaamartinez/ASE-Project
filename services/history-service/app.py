from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
import os
import json
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def wait_for_db(max_retries=30, retry_interval=2):
    """Wait for database to be ready"""
    print("Waiting for database connection...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'history-db'),
                database=os.environ.get('DB_NAME', 'history_db'),
                user=os.environ.get('DB_USER', 'user'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                port=os.environ.get('DB_PORT', '5432'),
                connect_timeout=5
            )
            conn.close()
            print("Database connection successful")
            return True
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"Database not ready, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"Failed to connect to database: {e}")
                return False

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
    """Initialize database"""
    if not wait_for_db():
        print("Cannot initialize database - connection failed")
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create matches table
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
        
        # Create match moves table
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
        print("History database initialized")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

@app.route('/history/<username>', methods=['GET'])
def get_player_history(username):
    """Get match history for a player"""
    try:
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
            
            # Determine result for requested player
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history/matches', methods=['POST'])
def save_match_result():
    """Save match result"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    required_fields = ['match_id', 'player1', 'player2', 'winner', 'scores']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert match
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
        
        # Insert moves if present
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
        return jsonify({"error": f"Save error: {str(e)}"}), 500
    
    finally:
        cur.close()
        conn.close()
    
    return jsonify({"message": "Match saved to history"}), 201

@app.route('/history/matches/<match_id>', methods=['GET'])
def get_match_details(match_id):
    """Get complete match details"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Match data
        cur.execute('''
            SELECT player1, player2, winner, scores, start_time, end_time
            FROM matches WHERE match_id = %s
        ''', (match_id,))
        
        match_data = cur.fetchone()
        if not match_data:
            return jsonify({"error": "Match not found"}), 404
        
        player1, player2, winner, scores, start_time, end_time = match_data
        
        # Match moves
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

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
    print("Initializing History Service database...")
    if init_db():
        print("History service starting on port 5005...")
        app.run(host='0.0.0.0', port=5005, debug=True)
    else:
        print("Failed to initialize database")