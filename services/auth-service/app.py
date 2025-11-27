from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# In-memory storage for demo
users_db = {}
sessions_db = {}

def create_player_in_player_service(username, email):
    """Create player profile in Player Service when user registers"""
    try:
        player_service_url = "http://player-service:5004"
        
        # Initialize player stats
        response = requests.put(
            f"{player_service_url}/players/{username}/stats",
            json={
                "match_result": "init",
                "score_delta": 0
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']

    if username in users_db:
        return jsonify({"error": "Username already exists"}), 400

    # Store user
    users_db[username] = {
        'password': data['password'],
        'email': data.get('email'),
        'created_at': datetime.now().isoformat()
    }

    # Create player profile in Player Service
    if create_player_in_player_service(username, data.get('email')):
        print(f"✅ Player profile created for {username}")
    else:
        print(f"⚠️  Could not create player profile for {username}")

    return jsonify({
        "message": "User registered successfully",
        "username": username
    }), 201

@app.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password = data['password']

    user = users_db.get(username)
    if not user or user['password'] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate JWT token
    token = jwt.encode({
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    # Store session
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        'username': username,
        'created_at': datetime.now().isoformat()
    }

    return jsonify({
        "message": "Login successful",
        "token": token,
        "session_id": session_id
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "Auth service is running"})

if __name__ == '__main__':
    print("✅ Auth service starting on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)
