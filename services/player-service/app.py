from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage (replace with DB later)
players_db = {}
player_stats_db = {}

@app.route('/players/<username>', methods=['GET'])
def get_player_profile(username):
    """Get player profile and stats"""
    player = players_db.get(username)
    stats = player_stats_db.get(username)
    
    if not player or not stats:
        return jsonify({"error": "Player not found"}), 404
        
    profile = {
        "player_id": player.get('player_id'),
        "username": username,
        "email": player.get('email'),
        "created_at": player.get('created_at'),
        "total_score": stats.get('total_score', 0),
        "level": stats.get('level', 1),
        "matches_played": stats.get('matches_played', 0),
        "matches_won": stats.get('matches_won', 0),
        "matches_lost": stats.get('matches_lost', 0),
        "win_rate": stats.get('win_rate', 0.0)
    }
    
    return jsonify(profile)

@app.route('/players/<username>/stats', methods=['PUT'])
def update_player_stats(username):
    """Update player stats after match"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "JSON data required"}), 400
        
    if username not in player_stats_db:
        # Initialize if doesn't exist
        player_stats_db[username] = {
            'total_score': 0,
            'level': 1,
            'matches_played': 0,
            'matches_won': 0,
            'matches_lost': 0,
            'win_rate': 0.0
        }
    
    stats = player_stats_db[username]
    
    # Update stats
    if 'match_result' in data:
        stats['matches_played'] += 1
        if data['match_result'] == 'win':
            stats['matches_won'] += 1
        else:
            stats['matches_lost'] += 1
            
        # Calculate win rate
        if stats['matches_played'] > 0:
            stats['win_rate'] = round(stats['matches_won'] / stats['matches_played'], 2)
    
    if 'score_delta' in data:
        stats['total_score'] = max(0, stats['total_score'] + data['score_delta'])
    
    return jsonify({"message": "Stats updated", "stats": stats})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Player service is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
