from flask import Flask, request, jsonify
import requests
import jwt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-super-secret-key-change-in-production')

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:5001"
CARDS_SERVICE_URL = "http://cards-service:5002"
MATCHES_SERVICE_URL = "http://matches-service:5003"
PLAYER_SERVICE_URL = "http://player-service:5004"
HISTORY_SERVICE_URL = "http://history-service:5005"

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    '/auth/register',
    '/auth/login', 
    '/auth/health',
    '/auth/validate-token',
    '/cards/cards',
    '/cards/health',
    '/health',
    '/players/health',
    '/matches/health',
    '/history/health'
]

def validate_jwt_token(token):
    """Validate JWT token with Auth Service"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/validate-token",
            json={"token": token},
            timeout=5
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json()
    except requests.exceptions.RequestException as e:
        return False, {"error": f"Auth service unavailable: {str(e)}"}

def extract_token_from_header():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None

def make_request(service_url, path, method):
    """Helper function to make requests to services"""
    try:
        url = f"{service_url}/{path}"
        
        # Prepare headers (remove Host to avoid conflicts)
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        
        # Prepare request arguments
        request_args = {
            'method': method,
            'url': url,
            'headers': headers,
            'params': request.args,
            'timeout': 10
        }
        
        # Only add JSON data for POST/PUT requests that have JSON content
        if method in ['POST', 'PUT'] and request.get_data():
            try:
                request_args['json'] = request.get_json()
            except:
                # If JSON parsing fails, send raw data
                request_args['data'] = request.get_data()
                request_args['headers']['Content-Type'] = request.content_type
        
        response = requests.request(**request_args)
        
        # Return the response from the service
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.before_request
def authenticate_request():
    """Authenticate requests before processing"""
    # Skip authentication for public endpoints
    if request.path in PUBLIC_ENDPOINTS:
        return None
    
    # Skip OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return None
    
    # Extract and validate JWT token
    token = extract_token_from_header()
    if not token:
        return jsonify({"error": "Authorization token required. Use: Authorization: Bearer <token>"}), 401
    
    is_valid, token_data = validate_jwt_token(token)
    if not is_valid:
        return jsonify({"error": token_data.get('error', 'Invalid token')}), 401
    
    # Add username to request context for downstream services
    request.username = token_data.get('username')
    
    return None

# Auth routes
@app.route('/auth/register', methods=['POST'])
def auth_register():
    return make_request(AUTH_SERVICE_URL, "register", "POST")

@app.route('/auth/login', methods=['POST'])
def auth_login():
    return make_request(AUTH_SERVICE_URL, "login", "POST")

@app.route('/auth/validate-token', methods=['POST'])
def auth_validate_token():
    return make_request(AUTH_SERVICE_URL, "validate-token", "POST")

@app.route('/auth/health', methods=['GET'])
def auth_health():
    return make_request(AUTH_SERVICE_URL, "health", "GET")

# Cards routes
@app.route('/cards/cards', methods=['GET'])
def cards_all():
    return make_request(CARDS_SERVICE_URL, "cards", "GET")

@app.route('/cards/cards/<int:card_id>', methods=['GET'])
def cards_specific(card_id):
    return make_request(CARDS_SERVICE_URL, f"cards/{card_id}", "GET")

@app.route('/cards/health', methods=['GET'])
def cards_health():
    return make_request(CARDS_SERVICE_URL, "health", "GET")

# Matches routes
@app.route('/matches/matches', methods=['POST'])
def matches_create():
    return make_request(MATCHES_SERVICE_URL, "matches", "POST")

@app.route('/matches/matches/<match_id>', methods=['GET'])
def matches_get(match_id):
    return make_request(MATCHES_SERVICE_URL, f"matches/{match_id}", "GET")

@app.route('/matches/matches/<match_id>/play', methods=['POST'])
def matches_play(match_id):
    return make_request(MATCHES_SERVICE_URL, f"matches/{match_id}/play", "POST")

@app.route('/matches/health', methods=['GET'])
def matches_health():
    return make_request(MATCHES_SERVICE_URL, "health", "GET")

# Player routes
@app.route('/players/<username>', methods=['GET'])
def players_get(username):
    return make_request(PLAYER_SERVICE_URL, f"players/{username}", "GET")

@app.route('/players/<username>/stats', methods=['PUT'])
def players_update_stats(username):
    return make_request(PLAYER_SERVICE_URL, f"players/{username}/stats", "PUT")

@app.route('/players/health', methods=['GET'])
def players_health():
    return make_request(PLAYER_SERVICE_URL, "health", "GET")

# History routes
@app.route('/history/<username>', methods=['GET'])
def history_get(username):
    return make_request(HISTORY_SERVICE_URL, f"history/{username}", "GET")

@app.route('/history/matches', methods=['POST'])
def history_save():
    return make_request(HISTORY_SERVICE_URL, "history/matches", "POST")

@app.route('/history/health', methods=['GET'])
def history_health():
    return make_request(HISTORY_SERVICE_URL, "health", "GET")

# API Gateway health
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "API Gateway is running", 
        "authentication": "JWT validation enabled",
        "public_endpoints": PUBLIC_ENDPOINTS,
        "services": {
            "auth": AUTH_SERVICE_URL,
            "cards": CARDS_SERVICE_URL,
            "matches": MATCHES_SERVICE_URL,
            "players": PLAYER_SERVICE_URL,
            "history": HISTORY_SERVICE_URL
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 API Gateway starting on port 5000...")
    print("🔐 JWT Authentication: ENABLED")
    print("📡 Public endpoints:", PUBLIC_ENDPOINTS)
    app.run(host='0.0.0.0', port=5000, debug=True)
