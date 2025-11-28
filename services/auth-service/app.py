from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid
import requests
import bcrypt
import psycopg2
import os
import time
from flask_cors import CORS  # AGGIUNGI QUESTO

app = Flask(__name__)
CORS(app)  # AGGIUNGI QUESTO PER IL FRONTEND
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-jwt-key-change-in-production-2025')

# Database connection with retry logic
def wait_for_db(max_retries=30, retry_interval=2):
    """Wait for database to be ready"""
    print("🔄 Waiting for database connection...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'auth-db'),
                database=os.environ.get('DB_NAME', 'auth_db'),
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
                print(f"⏳ Database not ready, retrying... ({i+1}/{max_retries}) - {str(e)}")
                time.sleep(retry_interval)
            else:
                print(f"❌ Failed to connect to database after {max_retries} attempts: {e}")
                return False

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
    if not wait_for_db():
        print("❌ Cannot initialize database - connection failed")
        return False
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
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
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def create_player_in_player_service(username, email=None):
    """Create player profile in Player Service when user registers"""
    try:
        # Wait a bit for player service to be ready
        time.sleep(2)
        player_service_url = "http://player-service:5004"
        
        response = requests.put(
            f"{player_service_url}/players/{username}/stats",
            json={
                "match_result": "init",
                "score_delta": 0
            },
            timeout=10
        )
        print(f"✅ Player profile creation response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️  Could not create player profile: {e}")
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

        # Hash password - USIAMO LA VERSIONE SICURA
        print(f"DEBUG: Hashing password for user: {username}")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        print(f"DEBUG: Generated hash type: {type(password_hash)}, length: {len(password_hash)}")

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
        print(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
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

        # DEBUG: Verifica il tipo di stored_hash
        print(f"DEBUG: Type of stored_hash: {type(stored_hash)}")
        
        # Converti stored_hash in bytes se necessario
        if isinstance(stored_hash, memoryview):
            stored_hash = stored_hash.tobytes()
        elif isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        elif hasattr(stored_hash, 'tobytes'):
            stored_hash = stored_hash.tobytes()
        
        # Converti la password in bytes
        password_bytes = password.encode('utf-8')
        
        print(f"DEBUG: Verifying password for user: {username}")
        print(f"DEBUG: Stored hash type: {type(stored_hash)}, length: {len(stored_hash) if stored_hash else 0}")
        
        # Verifica la password
        if not bcrypt.checkpw(password_bytes, stored_hash):
            print(f"DEBUG: Password verification failed for user: {username}")
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        print(f"DEBUG: Password verification successful for user: {username}")

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
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
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
        return jsonify({
            "status": "Auth service is running", 
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "Auth service is running", 
            "database": "disconnected", 
            "error": str(e)
        }), 503

if __name__ == '__main__':
    print("🚀 Starting Auth Service...")
    print("🔄 Initializing database...")
    if init_db():
        print("✅ Database initialized successfully")
        print("✅ Auth service starting on port 5001...")
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        print("❌ Failed to initialize database, service cannot start")



