from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# In-memory storage for demo
users_db = {}
sessions_db = {}

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
        'created_at': datetime.now().isoformat()
    }

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
    app.run(host='0.0.0.0', port=5001, debug=True)
EOF

# 3. Aggiorna requirements.txt (rimuovi psycopg2)
echo "Flask==2.3.3
PyJWT==2.8.0" > services/auth-service/requirements.txt

# 4. Aggiorna docker-compose.yml per rimuovere database da auth-service
cat > docker-compose.yml << 'EOF'
services:
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "5000:5000"
    depends_on:
      - auth-service
      - cards-service
      - matches-service
      - player-service
      - history-service

  auth-service:
    build: ./services/auth-service
    expose:
      - "5001"
    environment:
      - FLASK_ENV=development

  cards-service:
    build: ./services/cards-service
    expose:
      - "5002"
    environment:
      - FLASK_ENV=development

  matches-service:
    build: ./services/match-service
    expose:
      - "5003"
    environment:
      - FLASK_ENV=development

  player-service:
    build: ./services/player-service
    expose:
      - "5004"
    environment:
      - FLASK_ENV=development

  history-service:
    build: ./services/history-service
    expose:
      - "5005"
    environment:
      - FLASK_ENV=development
