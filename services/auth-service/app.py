from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid
import requests
import bcrypt
import psycopg2
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'auth-db'),
        database=os.environ.get('DB_NAME', 'auth_db'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE,
            password_hash BYTEA NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            account_status VARCHAR(20) DEFAULT 'active'
        )
    ''')
    
    # Create sessions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id UUID PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def create_player_in_player_service(username, email=None):
    """Create player profile in Player Service when user registers"""
    try:
        player_service_url = "http://player-service:5004"
        
        response = requests.put(
            f"{player_service_url}/players/{username}/stats",
            json={
                "match_result": "init",
                "score_delta": 0
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error creating player profile: {e}")
        return False

@app.route('/register', methods=['POST'])
def register():
    """Register a new user with password hashing"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password = data['password']
    email = data.get('email')

    # Validate password strength
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user already exists
        cur.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Username already exists"}), 400

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user
        cur.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
            (username, email, password_hash)
        )

        conn.commit()
        cur.close()
        conn.close()

        # Create player profile
        if create_player_in_player_service(username, email):
            print(f"✅ Player profile created for {username}")
        else:
            print(f"⚠️  Could not create player profile for {username}")

        return jsonify({
            "message": "User registered successfully",
            "username": username
        }), 201

    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password = data['password']

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get user from database
        cur.execute(
            'SELECT username, password_hash FROM users WHERE username = %s AND account_status = %s',
            (username, 'active')
        )
        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid credentials or inactive account"}), 401

        stored_username, stored_hash = user

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        # Update last login
        cur.execute(
            'UPDATE users SET last_login = %s WHERE username = %s',
            (datetime.now(), username)
        )

        # Generate JWT token
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

        # Store session
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=24)
        
        cur.execute(
            'INSERT INTO sessions (session_id, username, expires_at) VALUES (%s, %s, %s)',
            (session_id, username, expires_at)
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Login successful",
            "token": token,
            "session_id": session_id,
            "username": username
        })

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/validate-token', methods=['POST'])
def validate_token():
    """Validate JWT token"""
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({"error": "Token required"}), 400

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({"valid": True, "username": payload['username']})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({"status": "Auth service is running", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "Auth service is running", "database": "disconnected", "error": str(e)}), 503

if __name__ == '__main__':
    print("🔄 Initializing database...")
    init_db()
    print("✅ Auth service starting on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)
