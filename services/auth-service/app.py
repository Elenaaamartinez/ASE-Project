from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid
import requests
import bcrypt
import psycopg2
import os
import time
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)
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
        # Create users table with NULL allowed for email
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

def validate_input(data):
    """Validate and sanitize user input"""
    errors = []
    
    # Validate username
    username = data.get('username', '').strip()
    if not username:
        errors.append("Username is required")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters")
    elif len(username) > 50:
        errors.append("Username must be less than 50 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers and underscores")
    
    # Validate password - SEMPLIFICATA PER TESTING
    password = data.get('password', '')
    if not password:
        errors.append("Password is required")
    elif len(password) < 4:
        errors.append("Password must be at least 4 characters")
    # Commentato per testing - scommenta per produzione
    # elif not any(c.isupper() for c in password):
    #     errors.append("Password must contain at least one uppercase letter")
    # elif not any(c.islower() for c in password):
    #     errors.append("Password must contain at least one lowercase letter")
    # elif not any(c.isdigit() for c in password):
    #     errors.append("Password must contain at least one number")
    
    # Validate email if provided (email è opzionale)
    email = data.get('email', '').strip()
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("Invalid email format")
    
    return errors

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
    """Register a new user with password hashing and input validation"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data required"}), 400

    # Validate input
    validation_errors = validate_input(data)
    if validation_errors:
        return jsonify({"error": "Validation failed", "details": validation_errors}), 400

    username = data['username'].strip()
    password = data['password']
    email = data.get('email', '').strip()

    # Convert empty email to None to avoid unique constraint violations
    if email == '':
        email = None
        print(f"🔧 Email converted to None for user: {username}")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user already exists
        cur.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Username already exists"}), 400

        # Check if email already exists (only if email is provided and not None)
        if email:
            cur.execute('SELECT email FROM users WHERE email = %s', (email,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return jsonify({"error": "Email already exists"}), 400

        # Hash password with bcrypt
        print(f"🔒 Hashing password for user: {username}")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        print(f"🔒 Generated hash successfully for {username}")

        # Insert new user (email can be NULL)
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

    except psycopg2.IntegrityError as e:
        print(f"❌ Database integrity error: {e}")
        return jsonify({"error": "Registration failed: username or email already exists"}), 400
    except Exception as e:
        print(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token with input validation"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data required"}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

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

        # Convert stored_hash to bytes for bcrypt
        if isinstance(stored_hash, memoryview):
            stored_hash = stored_hash.tobytes()
        elif isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        elif hasattr(stored_hash, 'tobytes'):
            stored_hash = stored_hash.tobytes()
        
        # Verify password
        password_bytes = password.encode('utf-8')
        
        print(f"🔒 Verifying password for user: {username}")
        
        if not bcrypt.checkpw(password_bytes, stored_hash):
            print(f"🔒 Password verification failed for user: {username}")
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401

        print(f"🔒 Password verification successful for user: {username}")

        # Update last login
        cur.execute(
            'UPDATE users SET last_login = %s WHERE username = %s',
            (datetime.now(), username)
        )

        # Generate JWT token
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

        # Generate refresh token
        refresh_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        refresh_token = jwt.encode(refresh_payload, app.config['SECRET_KEY'], algorithm='HS256')

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
            "refresh_token": refresh_token,
            "session_id": session_id,
            "username": username,
            "expires_in": 86400  # 24 hours in seconds
        })

    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh JWT token using refresh token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    try:
        payload = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        if payload.get('type') != 'refresh':
            return jsonify({"error": "Invalid token type"}), 401

        username = payload['username']

        # Generate new access token
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        new_token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            "token": new_token,
            "expires_in": 86400
        })

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid refresh token"}), 401

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

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and invalidate session"""
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"error": "Session ID required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('DELETE FROM sessions WHERE session_id = %s', (session_id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": "Logout successful"})

    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        users_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({
            "status": "Auth service is running", 
            "database": "connected",
            "users_count": users_count,
            "timestamp": datetime.now().isoformat(),
            "security": "bcrypt+jwt+validation"
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
        print("🔒 Security features: bcrypt, JWT, input validation")
        print("📧 Email handling: NULL allowed for empty emails")
        app.run(host='0.0.0.0', port=5001, debug=False)
    else:
        print("❌ Failed to initialize database, service cannot start")
