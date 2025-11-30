from flask import Flask, request, jsonify
import uuid
import os
import psycopg2
import time
from datetime import datetime
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
                host=os.environ.get('DB_HOST', 'player-db'),
                database=os.environ.get('DB_NAME', 'player_db'),
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
        host=os.environ.get('DB_HOST', 'player-db'),
        database=os.environ.get('DB_NAME', 'player_db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )
    return conn

def init_db():
    """Initialize database tables"""
    if not wait_for_db():
        print("❌ Cannot initialize database - connection failed")
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create players table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS players (
                username VARCHAR(50) PRIMARY KEY,
                player_id UUID NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create player stats table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                username VARCHAR(50) PRIMARY KEY,
                total_score BIGINT DEFAULT 0,
                level INTEGER DEFAULT 1,
                matches_played INTEGER DEFAULT 0,
                matches_won INTEGER DEFAULT 0,
                matches_lost INTEGER DEFAULT 0,
                win_rate NUMERIC(5,4) DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def ensure_player_exists(username, email=None):
    """Insert player and stats if not exist (idempotent)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if player exists
        cur.execute('SELECT username FROM players WHERE username = %s', (username,))
        if not cur.fetchone():
            cur.execute(
                'INSERT INTO players (username, player_id, email) VALUES (%s, %s, %s)',
                (username, str(uuid.uuid4()), email)
            )
            print(f"✅ Created player record for {username}")
    
        # Check if stats exist
        cur.execute('SELECT username FROM player_stats WHERE username = %s', (username,))
        if not cur.fetchone():
            cur.execute(
                '''INSERT INTO player_stats (username, total_score, level, matches_played, matches_won, matches_lost, win_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (username, 0, 1, 0, 0, 0, 0.0)
            )
            print(f"✅ Created stats record for {username}")
    
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error ensuring player exists: {e}")
        conn.rollback()
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

@app.route('/players/<username>', methods=['GET'])
def get_player_profile(username):
    """Get player profile with validation"""
    if not validate_username(username):
        return jsonify({"error": "Invalid username format"}), 400
    
    try:
        ensure_player_exists(username)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get player basic info
        cur.execute('''
            SELECT p.player_id, p.email, p.created_at, 
                   ps.total_score, ps.level, ps.matches_played, 
                   ps.matches_won, ps.matches_lost, ps.win_rate,
                   ps.last_updated
            FROM players p
            LEFT JOIN player_stats ps ON p.username = ps.username
            WHERE p.username = %s
        ''', (username,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({"error": "Player not found"}), 404
        
        (player_id, email, created_at, total_score, level, 
         matches_played, matches_won, matches_lost, win_rate, last_updated) = result
        
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
            "win_rate": float(win_rate) if win_rate else 0.0,
            "last_updated": last_updated.isoformat() if last_updated else None
        }
        
        return jsonify(profile), 200
        
    except Exception as e:
        print(f"❌ Error getting player profile: {e}")
        return jsonify({"error": f"Failed to get player profile: {str(e)}"}), 500

@app.route('/players/<username>/stats', methods=['PUT'])
def update_player_stats(username):
    """Update player stats after a match"""
    if not validate_username(username):
        return jsonify({"error": "Invalid username format"}), 400
    
    try:
        data = request.get_json() or {}
        
        # Validate input data
        match_result = data.get('match_result')
        if match_result not in ['win', 'loss', 'draw', 'init']:
            return jsonify({"error": "Invalid match_result. Must be 'win', 'loss', 'draw', or 'init'"}), 400
        
        score_delta = data.get('score_delta', 0)
        if not isinstance(score_delta, (int, float)):
            return jsonify({"error": "score_delta must be a number"}), 400
        
        ensure_player_exists(username)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get current stats
        cur.execute('''
            SELECT total_score, matches_played, matches_won, matches_lost 
            FROM player_stats WHERE username = %s
        ''', (username,))
        
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "Player stats not found"}), 404
        
        total_score, matches_played, matches_won, matches_lost = result
        
        # Update based on match result
        if match_result != 'init':  # 'init' is for player creation, don't count as match
            matches_played += 1
            if match_result == 'win':
                matches_won += 1
            elif match_result == 'loss':
                matches_lost += 1
            # For 'draw', no change to wins/losses
        
        # Update score (ensure it doesn't go negative)
        total_score = max(0, total_score + score_delta)
        
        # Calculate win rate
        win_rate = (matches_won / matches_played) if matches_played > 0 else 0.0
        
        # Update level based on score (level up every 1000 points)
        level = 1 + (total_score // 1000)
        
        # Update database
        cur.execute('''
            UPDATE player_stats 
            SET total_score = %s, level = %s, matches_played = %s,
                matches_won = %s, matches_lost = %s, win_rate = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE username = %s
        ''', (total_score, level, matches_played, matches_won, matches_lost, win_rate, username))
        
        conn.commit()
        cur.close()
        conn.close()
        
        updated_stats = {
            "total_score": total_score,
            "level": level,
            "matches_played": matches_played,
            "matches_won": matches_won,
            "matches_lost": matches_lost,
            "win_rate": round(win_rate, 4)
        }
        
        print(f"✅ Updated stats for {username}: {updated_stats}")
        
        return jsonify({
            "message": "Stats updated successfully",
            "stats": updated_stats
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating player stats: {e}")
        return jsonify({"error": f"Failed to update stats: {str(e)}"}), 500

@app.route('/players/<username>/stats', methods=['GET'])
def get_player_stats(username):
    """Get only player stats"""
    if not validate_username(username):
        return jsonify({"error": "Invalid username format"}), 400
    
    try:
        ensure_player_exists(username)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT total_score, level, matches_played, matches_won, matches_lost, win_rate
            FROM player_stats WHERE username = %s
        ''', (username,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return jsonify({"error": "Player stats not found"}), 404
        
        total_score, level, matches_played, matches_won, matches_lost, win_rate = result
        
        stats = {
            "username": username,
            "total_score": total_score,
            "level": level,
            "matches_played": matches_played,
            "matches_won": matches_won,
            "matches_lost": matches_lost,
            "win_rate": float(win_rate) if win_rate else 0.0
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get player stats: {str(e)}"}), 500

@app.route('/players', methods=['GET'])
def list_players():
    """List all players with basic info (for admin/lobby)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT p.username, p.player_id, ps.total_score, ps.level, ps.matches_played
            FROM players p
            LEFT JOIN player_stats ps ON p.username = ps.username
            ORDER BY ps.total_score DESC
            LIMIT 100
        ''')
        
        players = []
        for row in cur.fetchall():
            username, player_id, total_score, level, matches_played = row
            players.append({
                "username": username,
                "player_id": str(player_id),
                "total_score": total_score,
                "level": level,
                "matches_played": matches_played
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "players": players,
            "count": len(players)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to list players: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            "status": "Player service is running",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "Player service is running",
            "database": "disconnected",
            "error": str(e)
        }), 503

if __name__ == '__main__':
    print("👤 Initializing Player Service database...")
    if init_db():
        print("✅ Player service starting on port 5004...")
        print("📊 Player profiles and statistics system ready")
        app.run(host='0.0.0.0', port=5004, debug=False)
    else:
        print("❌ Failed to initialize database")
