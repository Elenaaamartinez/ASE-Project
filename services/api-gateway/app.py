from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS
import jwt
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:5001"
CARDS_SERVICE_URL = "http://cards-service:5002"
MATCH_SERVICE_URL = "http://match-service:5003"
PLAYER_SERVICE_URL = "http://player-service:5004"
HISTORY_SERVICE_URL = "http://history-service:5005"

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production-2025')

def validate_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return {"valid": True, "username": payload['username']}
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return {"valid": False, "error": "Invalid or expired token"}

def requires_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path in ['/health', '/auth/register', '/auth/login', '/cards/cards']:
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header required"}), 401
        
        token = auth_header.split(' ')[1]
        validation = validate_token(token)
        if not validation['valid']:
            return jsonify({"error": validation['error']}), 401
        
        request.username = validation['username']
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
@requires_auth
def before_request():
    pass

def forward_request(service_url, path, method):
    try:
        url = f"{service_url}/{path}"
        request_args = {
            'method': method,
            'url': url,
            'headers': {k: v for k, v in request.headers.items() if k != 'Host'},
        }
        if method in ['POST', 'PUT', 'PATCH']:
            if request.is_json:
                request_args['json'] = request.get_json()
            else:
                request_args['data'] = request.get_data()
        
        response = requests.request(**request_args)
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROUTES ---

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "API Gateway running", "timestamp": datetime.now().isoformat()})

# Auth
@app.route('/auth/register', methods=['POST'])
def auth_register(): return forward_request(AUTH_SERVICE_URL, "register", "POST")

@app.route('/auth/login', methods=['POST'])
def auth_login(): return forward_request(AUTH_SERVICE_URL, "login", "POST")

@app.route('/auth/logout', methods=['POST'])
def auth_logout(): return forward_request(AUTH_SERVICE_URL, "logout", "POST")

@app.route('/auth/health', methods=['GET'])
def auth_health(): return forward_request(AUTH_SERVICE_URL, "health", "GET")

# Cards
@app.route('/cards/cards', methods=['GET'])
def cards_all(): return forward_request(CARDS_SERVICE_URL, "cards", "GET")

@app.route('/cards/cards/<card_id>', methods=['GET'])
def cards_specific(card_id): return forward_request(CARDS_SERVICE_URL, f"cards/{card_id}", "GET")

@app.route('/cards/health', methods=['GET'])
def cards_health(): return forward_request(CARDS_SERVICE_URL, "health", "GET")

# Matches (Plurale esterno -> Singolare interno)
@app.route('/matches/matches', methods=['POST'])
def match_create(): return forward_request(MATCH_SERVICE_URL, "match", "POST")

@app.route('/matches/matches', methods=['GET'])
def match_list(): return forward_request(MATCH_SERVICE_URL, "match", "GET")

@app.route('/matches/matches/<match_id>', methods=['GET'])
def match_get(match_id): return forward_request(MATCH_SERVICE_URL, f"match/{match_id}", "GET")

@app.route('/matches/matches/<match_id>/play', methods=['POST'])
def match_play(match_id): return forward_request(MATCH_SERVICE_URL, f"match/{match_id}/play", "POST")

@app.route('/matches/health', methods=['GET'])
def match_health(): return forward_request(MATCH_SERVICE_URL, "health", "GET")

# Players
@app.route('/players/<username>', methods=['GET'])
def players_get(username): return forward_request(PLAYER_SERVICE_URL, f"players/{username}", "GET")

@app.route('/players', methods=['GET'])
def players_list(): return forward_request(PLAYER_SERVICE_URL, "players", "GET")

@app.route('/players/health', methods=['GET'])
def players_health(): return forward_request(PLAYER_SERVICE_URL, "health", "GET")

# History (CORRETTO: Ora punta a /matches plurale)
@app.route('/history/<username>', methods=['GET'])
def history_get(username): return forward_request(HISTORY_SERVICE_URL, f"history/{username}", "GET")

@app.route('/history/stats/<username>', methods=['GET'])
def history_stats(username): return forward_request(HISTORY_SERVICE_URL, f"stats/{username}", "GET")

# FIX QUI SOTTO: history/matches (plurale)
@app.route('/history/matches', methods=['POST'])
def history_save(): return forward_request(HISTORY_SERVICE_URL, "history/matches", "POST")

@app.route('/history/matches/<match_id>', methods=['GET'])
def history_match_details(match_id): return forward_request(HISTORY_SERVICE_URL, f"history/matches/{match_id}", "GET")

@app.route('/history/health', methods=['GET'])
def history_health(): return forward_request(HISTORY_SERVICE_URL, "health", "GET")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
