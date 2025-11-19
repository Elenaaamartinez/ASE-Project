# services/auth/app.py
from flask import Flask, request, jsonify
import sqlite3
import jwt
import datetime
from functools import wraps
import bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')

def init_db():
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Auth service healthy'})

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({'error': 'Missing required fields'}), 400
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                  (username, password_hash, email))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            return jsonify({'token': token})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
