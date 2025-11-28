from flask import Flask, request, jsonify
import uuid
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'player-service-secret-key'

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'player'),
        database=os.environ.get('DB_NAME', 'player'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )
    return conn

def init_db():
    """Create players and player_stats if they dont exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            username VARCHAR(50) PRIMARY KEY,
            player_id UUID NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            username VARCHAR(50) PRIMARY KEY,
            total_score BIGINT DEFAULT 0,
            level INT DEFAULT 1,
            matches_played INT DEFAULT 0,
            matches_won INT DEFAULT 0,
            matches_lost INT DEFAULT 0,
            win_rate NUMERIC(5,4) DEFAULT 0,
            FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    cur.close()
    conn.close()
    
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
    """Give back the profile + stats; auto-initializes not exist (compatible with auth-service)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT player_id, email, created_at FROM players WHERE username = %s', (username,))
    p = cur.fetchone()

    if not p:
        # auto-init if not present
        ensure_player_exists(username)
        cur.execute('SELECT player_id, email, created_at FROM players WHERE username = %s', (username,))
        p = cur.fetchone()

    player_id, email, created_at = p

    cur.execute('SELECT total_score, level, matches_played, matches_won, matches_lost, win_rate FROM player_stats WHERE username = %s', (username,))
    s = cur.fetchone()
    cur.close()
    conn.close()

    if not s:
        # fallback (shouldn't happen)
        stats = {
            "total_score": 0,
            "level": 1,
            "matches_played": 0,
            "matches_won": 0,
            "matches_lost": 0,
            "win_rate": 0.0
        }
    else:
        total_score, level, matches_played, matches_won, matches_lost, win_rate = s
        stats = {
            "total_score": total_score,
            "level": level,
            "matches_played": matches_played,
            "matches_won": matches_won,
            "matches_lost": matches_lost,
            "win_rate": float(win_rate)
        }

    profile = {
        "player_id": str(player_id),
        "username": username,
        "email": email,
        "created_at": created_at.isoformat() if created_at else None,
        **stats
    }

    return jsonify(profile), 200

@app.route('/players/<username>/stats', methods=['PUT'])
def update_player_stats(username):
    """
    Endpoint use by auth-service for initialization:
      PUT /players/<username>/stats  with {"match_result":"init","score_delta":0}
    Also used to update stats after matches:
      {"match_result":"win"|"loss", "score_delta": int}
    """
    data = request.get_json() or {}

    # Create player + stats if necessary (auth-service expects that)
    ensure_player_exists(username, data.get('email'))

    conn = get_db_connection()
    cur = conn.cursor()

    # handle init
    if data.get('match_result') == 'init':
        cur.execute('SELECT total_score, level, matches_played, matches_won, matches_lost, win_rate FROM player_stats WHERE username = %s', (username,))
        s = cur.fetchone()
        cur.close()
        conn.close()
        if s:
            total_score, level, matches_played, matches_won, matches_lost, win_rate = s
            stats = {
                "total_score": total_score,
                "level": level,
                "matches_played": matches_played,
                "matches_won": matches_won,
                "matches_lost": matches_lost,
                "win_rate": float(win_rate)
            }
        else:
            stats = {
                "total_score": 0,
                "level": 1,
                "matches_played": 0,
                "matches_won": 0,
                "matches_lost": 0,
                "win_rate": 0.0
            }
        return jsonify({"message": "Player initialized", "stats": stats}), 200

    # apply real update
    # retrieve current stats
    cur.execute('SELECT total_score, matches_played, matches_won, matches_lost FROM player_stats WHERE username = %s FOR UPDATE', (username,))
    row = cur.fetchone()
    if not row:
        # ensure exists and try again (race safety)
        cur.close()
        conn.close()
        ensure_player_exists(username, data.get('email'))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT total_score, matches_played, matches_won, matches_lost FROM player_stats WHERE username = %s FOR UPDATE', (username,))
        row = cur.fetchone()

    total_score, matches_played, matches_won, matches_lost = row

    # update matches
    match_result = data.get('match_result')
    if match_result in ('win', 'loss'):
        matches_played += 1
        if match_result == 'win':
            matches_won += 1
        else:
            matches_lost += 1

    # update score
    score_delta = int(data.get('score_delta', 0))
    total_score = max(0, total_score + score_delta)

    # calculate win rate
    win_rate = (matches_won / matches_played) if matches_played > 0 else 0.0

    # optional level-up logic (simple example)
    level = 1 + (total_score // 1000)

    # persist
    cur.execute('''
        UPDATE player_stats SET total_score = %s, level = %s, matches_played = %s,
                             matches_won = %s, matches_lost = %s, win_rate = %s
        WHERE username = %s
    ''', (total_score, level, matches_played, matches_won, matches_lost, win_rate, username))

    conn.commit()
    cur.close()
    conn.close()

    stats = {
        "total_score": total_score,
        "level": level,
        "matches_played": matches_played,
        "matches_won": matches_won,
        "matches_lost": matches_lost,
        "win_rate": round(win_rate, 4)
    }

    return jsonify({"message": "Stats updated", "stats": stats}), 200

@app.route('/players', methods=['POST'])
def create_player():
    """Create a new player (idempotent)"""
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')

    if not username:
        return jsonify({"error": "username required"}), 400

    try:
        ensure_player_exists(username, email)
        return jsonify({"message": "Player created or already existed", "username": username}), 201
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
        return jsonify({"status": f"{app.config['SERVICE_NAME']} is running", "database": "connected"})
    except Exception as e:
        return jsonify({"status": f"{app.config['SERVICE_NAME']} is running", "database": "disconnected", "error": str(e)}), 503

if __name__ == '__main__':
    print("Initializing database of player-service...")
    init_db()
    print("Player service starting on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=True)
    
