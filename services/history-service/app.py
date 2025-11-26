from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage (replace with DB later)
match_history = []

@app.route('/history/<username>', methods=['GET'])
def get_player_history(username):
    """Get player's match history"""
    player_matches = [
        match for match in match_history 
        if match['player1'] == username or match['player2'] == username
    ]
    
    return jsonify({
        "username": username,
        "match_count": len(player_matches),
        "matches": player_matches
    })

@app.route('/history/matches', methods=['POST'])
def save_match_result():
    """Save completed match to history"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "JSON data required"}), 400
        
    required_fields = ['match_id', 'player1', 'player2', 'winner', 'scores']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    
    match_record = {
        "match_id": data['match_id'],
        "player1": data['player1'],
        "player2": data['player2'],
        "winner": data['winner'],
        "scores": data['scores'],
        "end_time": datetime.now().isoformat(),
        "moves": data.get('moves', [])
    }
    
    match_history.append(match_record)
    
    return jsonify({"message": "Match saved to history"}), 201

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "History service is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
