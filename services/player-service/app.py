from flask import Flask, request, jsonify
import uuid
import os
import psycopg2
from datetime import datetime
from flask_cors import CORS  # AGGIUNGI

app = Flask(__name__)
CORS(app)  # AGGIUNGI

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'player-db'),
        database=os.environ.get('DB_NAME', 'player_db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )
    return conn

def ensure_player_exists(username, email=None):
    """Insert player and stats if not exist (idempotent)"""
    conn = get_db_connection()
    cur = conn.cursor()

    # player
    cur.execute('SELECT username FROM players WHERE username = %s', (username,))
    if not cur.fetchone():
        cur.execute(
            'INSERT INTO players (username, player_id, email, created_at) VALUES (%s, %s, %s, %s)',
            (username, str(uuid.uuid4()), email, datetime.utcnow())
        )

    # stats
    cur.execute('SELECT username FROM player_stats WHERE username = %s', (username,))
    if not cur.fetchone():
        cur.execute(
            '''INSERT INTO player_stats (username, total_score, level, matches_played, matches_won, matches_lost, win_rate)
               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            (username, 0, 1, 0, 0, 0, 0.0)
        )

    conn.commit()
    cur.close()
    conn.close()

@app.route('/players/<username>', methods=['GET'])
def get_player_profile(username):
    """Get player profile"""
    try:
        ensure_player_exists(username)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT player_id, email, created_at FROM players WHERE username = %s', (username,))
        player_data = cur.fetchone()
        
        cur.execute('SELECT total_score, level, matches_played, matches_won, matches_lost, win_rate FROM player_stats WHERE username = %s', (username,))
        stats_data = cur.fetchone()
        
        cur.close()
        conn.close()

        if player_data and stats_data:
            player_id, email, created_at = player_data
            total_score, level, matches_played, matches_won, matches_lost, win_rate = stats_data
            
            profile = {
                "player_id": str(player_id),
                "username": username,
                "email": email,
                "created_at": created_at.isoformat() if created_at else None,
                "total_score": total_score,
                "level": level,
                "matches_played": matches_played,
                "matches_won": matches_won,
                "matches_lost": matches_lost,
                "win_rate": float(win_rate)
            }
            return jsonify(profile), 200
        else:
            return jsonify({"error": "Player not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/players/<username>/stats', methods=['PUT'])
def update_player_stats(username):
    """Update player stats"""
    try:
        data = request.get_json() or {}
        ensure_player_exists(username)

        conn = get_db_connection()
        cur = conn.cursor()

        # Get current stats
        cur.execute('SELECT total_score, matches_played, matches_won, matches_lost FROM player_stats WHERE username = %s', (username,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "Player stats not found"}), 404
            
        total_score, matches_played, matches_won, matches_lost = result

        # Update based on match result
        match_result = data.get('match_result')
        if match_result in ['win', 'loss']:
            matches_played += 1
            if match_result == 'win':
                matches_won += 1
            else:
                matches_lost += 1

        # Update score
        score_delta = data.get('score_delta', 0)
        total_score = max(0, total_score + score_delta)

        # Calculate win rate
        win_rate = (matches_won / matches_played) if matches_played > 0 else 0.0

        # Update level based on score
        level = 1 + (total_score // 1000)

        # Save to database
        cur.execute('''
            UPDATE player_stats 
            SET total_score = %s, level = %s, matches_played = %s,
                matches_won = %s, matches_lost = %s, win_rate = %s
            WHERE username = %s
        ''', (total_score, level, matches_played, matches_won, matches_lost, win_rate, username))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Stats updated",
            "stats": {
                "total_score": total_score,
                "level": level,
                "matches_played": matches_played,
                "matches_won": matches_won,
                "matches_lost": matches_lost,
                "win_rate": round(win_rate, 4)
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            "status": "Player service is running", 
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "Player service is running", 
            "database": "disconnected",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    print("✅ Player service starting on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=True)

