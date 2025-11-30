from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
import os
import json
import time
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

def wait_for_db(max_retries=30, retry_interval=2):
    """Wait for database to be ready"""
    print("🔄 Waiting for database connection...")
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
            print("✅ Database connection successful")
            return True
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"⏳ Database not ready, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"❌ Failed to connect to database after {max_retries} attempts: {e}")
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
        print("❌ Cannot initialize database - connection failed")
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
                FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for better performance
        cur.execute('CREATE INDEX IF NOT EXISTS idx_matches_player1 ON matches(player1)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_matches_player2 ON matches(player2)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_matches_end_time ON matches(end_time)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_match_moves_match_id ON match_moves(match_id)')
        
        conn.commit()
        print("✅ History database initialized with indexes")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def validate_username(username):
    """Validate username format"""
    if not username or not isinstance(username, str):
        return False
    if len(username) < 3 or len(username) > 50:
        return False
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    return True

def validate_match_data(data):
    """Validate match data before saving"""
    errors = []
    
    required_fields = ['match_id', 'player1', 'player2', 'winner', 'scores']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if 'match_id' in data and len(data['match_id']) > 100:
        errors.append("match_id too long")
    
    if 'player1' in data and not validate_username(data['player1']):
        errors.append("Invalid player1 username")
    
    if 'player2' in data and not validate_username(data['player2']):
        errors.append("Invalid player2 username")
    
    if 'scores' in data and not isinstance(data['scores'], dict):
        errors.append("Scores must be a JSON object")
    
    return errors

@app.route('/history/<username>', methods=['GET'])
def get_player_history(username):
    """Get match history for a player with pagination"""
    if not validate_username(username):
        return jsonify({"error": "Invalid username format"}), 400
    
    try:
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 records
        offset = max(int(request.args.get('offset', 0)), 0)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total count
        cur.execute('''
            SELECT COUNT(*) FROM matches 
            WHERE player1 = %s OR player2 = %s
        ''', (username, username))
        total_count = cur.fetchone()[0]
        
        # Get matches with pagination
        cur.execute('''
            SELECT match_id, player1, player2, winner, scores, start_time, end_time
            FROM matches
            WHERE player1 = %s OR player2 = %s
            ORDER BY end_time DESC NULLS LAST, start_time DESC
            LIMIT %s OFFSET %s
        ''', (username, username, limit, offset))
        
        matches = []
        for row in cur.fetchall():
            match_id, player1, player2, winner, scores, start_time, end_time = row
            
            # Determine result for requested player
            if winner == username:
                result = "win"
            elif winner == "draw":
                result = "draw"
            elif winner is None:
                result = "unknown"
            else:
                result = "loss"
            
            # Calculate duration if both times are available
            duration = None
            if start_time and end_time:
                duration = int((end_time - start_time).total_seconds())
            
            match_info = {
                "match_id": match_id,
                "player1": player1,
                "player2": player2,
                "winner": winner,
                "your_result": result,
                "scores": scores,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "duration_seconds": duration
            }
            matches.append(match_info)
        
        cur.close()
        conn.close()
        
        return jsonify({
            "username": username,
            "total_matches": total_count,
            "returned_matches": len(matches),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(matches)) < total_count
            },
            "matches": matches
        })
    except Exception as e:
        print(f"❌ Error getting player history: {e}")
        return jsonify({"error": f"Failed to get history: {str(e)}"}), 500

@app.route('/history/matches', methods=['POST'])
def save_match_result():
    """Save match result with validation"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    # Validate input data
    validation_errors = validate_match_data(data)
    if validation_errors:
        return jsonify({"error": "Validation failed", "details": validation_errors}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if match already exists
        cur.execute('SELECT match_id FROM matches WHERE match_id = %s', (data['match_id'],))
        if cur.fetchone():
            return jsonify({"error": "Match already exists"}), 409
        
        # Insert match
        cur.execute('''
            INSERT INTO matches (match_id, player1, player2, winner, scores, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['match_id'],
            data['player1'],
            data['player2'],
            data['winner'],
            json.dumps(data['scores']),
            data.get('start_time'),
            data.get('end_time', datetime.now())
        ))
        
        # Insert moves if present
        moves = data.get('moves', [])
        move_count = 0
        for move in moves:
            # Validate move data
            if not all(k in move for k in ['player', 'card_played', 'result']):
                continue
                
            cur.execute('''
                INSERT INTO match_moves (match_id, player, card_played, captured_cards, move_result, move_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                data['match_id'],
                move['player'],
                move['card_played'],
                json.dumps(move.get('captured_cards', [])),
                move['result'],
                move.get('timestamp', datetime.now())
            ))
            move_count += 1
        
        conn.commit()
        
        print(f"✅ Saved match {data['match_id']} with {move_count} moves")
        
        return jsonify({
            "message": "Match saved to history",
            "match_id": data['match_id'],
            "moves_saved": move_count
        }), 201
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving match: {e}")
        return jsonify({"error": f"Save error: {str(e)}"}), 500
    
    finally:
        cur.close()
        conn.close()

@app.route('/history/matches/<match_id>', methods=['GET'])
def get_match_details(match_id):
    """Get complete match details including all moves"""
    if not match_id or len(match_id) > 100:
        return jsonify({"error": "Invalid match_id"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Match data
        cur.execute('''
            SELECT player1, player2, winner, scores, start_time, end_time, status
            FROM matches WHERE match_id = %s
        ''', (match_id,))
        
        match_data = cur.fetchone()
        if not match_data:
            return jsonify({"error": "Match not found"}), 404
        
        player1, player2, winner, scores, start_time, end_time, status = match_data
        
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
        
        # Calculate some statistics
        player1_moves = len([m for m in moves if m['player'] == player1])
        player2_moves = len([m for m in moves if m['player'] == player2])
        scopas = len([m for m in moves if m['result'] == 'scopa'])
        
        return jsonify({
            "match_id": match_id,
            "player1": player1,
            "player2": player2,
            "winner": winner,
            "status": status,
            "scores": scores,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "statistics": {
                "total_moves": len(moves),
                "player1_moves": player1_moves,
                "player2_moves": player2_moves,
                "scopas": scopas
            },
            "moves": moves
        })
    except Exception as e:
        print(f"❌ Error getting match details: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/history/stats/<username>', methods=['GET'])
def get_player_statistics(username):
    """Get detailed statistics for a player"""
    if not validate_username(username):
        return jsonify({"error": "Invalid username format"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Basic match statistics
        cur.execute('''
            SELECT 
                COUNT(*) as total_matches,
                COUNT(CASE WHEN winner = %s THEN 1 END) as wins,
                COUNT(CASE WHEN winner != %s AND winner != 'draw' THEN 1 END) as losses,
                COUNT(CASE WHEN winner = 'draw' THEN 1 END) as draws,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds
            FROM matches 
            WHERE player1 = %s OR player2 = %s
        ''', (username, username, username, username))
        
        stats_row = cur.fetchone()
        total_matches, wins, losses, draws, avg_duration = stats_row
        
        # Recent activity (last 30 days)
        cur.execute('''
            SELECT COUNT(*) as recent_matches
            FROM matches
            WHERE (player1 = %s OR player2 = %s) 
            AND end_time >= CURRENT_DATE - INTERVAL '30 days'
        ''', (username, username))
        
        recent_matches = cur.fetchone()[0]
        
        # Most common opponent
        cur.execute('''
            SELECT 
                CASE 
                    WHEN player1 = %s THEN player2 
                    ELSE player1 
                END as opponent,
                COUNT(*) as matches_against
            FROM matches
            WHERE player1 = %s OR player2 = %s
            GROUP BY opponent
            ORDER BY matches_against DESC
            LIMIT 1
        ''', (username, username, username))
        
        common_opponent_row = cur.fetchone()
        common_opponent = common_opponent_row[0] if common_opponent_row else None
        matches_vs_opponent = common_opponent_row[1] if common_opponent_row else 0
        
        cur.close()
        conn.close()
        
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        statistics = {
            "username": username,
            "total_matches": total_matches,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(win_rate, 2),
            "recent_activity_30_days": recent_matches,
            "most_common_opponent": common_opponent,
            "matches_vs_common_opponent": matches_vs_opponent,
            "average_match_duration_seconds": round(float(avg_duration or 0), 2)
        }
        
        return jsonify(statistics)
        
    except Exception as e:
        print(f"❌ Error getting player statistics: {e}")
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500

@app.route('/history/matches/<match_id>', methods=['DELETE'])
def delete_match(match_id):
    """Delete a match and its moves (admin only)"""
    if not match_id or len(match_id) > 100:
        return jsonify({"error": "Invalid match_id"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Delete moves first (foreign key constraint)
        cur.execute('DELETE FROM match_moves WHERE match_id = %s', (match_id,))
        # Delete match
        cur.execute('DELETE FROM matches WHERE match_id = %s', (match_id,))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Match not found"}), 404
        
        conn.commit()
        return jsonify({"message": "Match deleted successfully"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to delete match: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check matches table
        cur.execute('SELECT COUNT(*) FROM matches')
        matches_count = cur.fetchone()[0]
        
        # Check moves table
        cur.execute('SELECT COUNT(*) FROM match_moves')
        moves_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "History service is running",
            "database": "connected",
            "statistics": {
                "matches_stored": matches_count,
                "moves_stored": moves_count
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "History service is running",
            "database": "disconnected",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    print("📜 Initializing History Service database...")
    if init_db():
        print("✅ History service starting on port 5005...")
        print("📊 Match history and statistics system ready")
        app.run(host='0.0.0.0', port=5005, debug=False)
    else:
        print("❌ Failed to initialize database")
