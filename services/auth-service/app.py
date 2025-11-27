import os
import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import jwt
import uuid
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password_hash = hash_password(data['password'])
    email = data.get('email')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            'INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)',
            (username, password_hash, email)
        )
        conn.commit()
    except psycopg2.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({
        "message": "User registered successfully",
        "username": username
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password required"}), 400

    username = data['username']
    password_hash = hash_password(data['password'])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username, password_hash FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or user[1] != password_hash:
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        "message": "Login successful",
        "token": token
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Auth service is running"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
