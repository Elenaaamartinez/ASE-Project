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

# JWT Secret for token validation
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production-2025')

def validate_token(token):
    """Validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return {"valid": True, "username": payload['username']}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}

def requires_auth(f):
    """Decorator for endpoints that require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth for health checks and public endpoints
        if request.path in ['/health', '/auth/register', '/auth/login', '/cards/cards']:
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header required with Bearer token"}), 401
        
        token = auth_header.split(' ')[1]
        validation_result = validate_token(token)
        
        if not validation_result['valid']:
            return jsonify({"error": validation_result['error']}), 401
        
        # Add username to request context for use in routes
        request.username = validation_result['username']
        return f(*args, **kwargs)
    
    return decorated_function

@app.before_request
@requires_auth
def before_request():
    """Apply authentication to all routes"""
    pass

def forward_request(service_url, path, method):
    """Forward request to appropriate service with error handling"""
    try:
        url = f"{service_url}/{path}"
        
        # Prepare request
        request_args = {
            'method': method,
            'url': url,
            'timeout': 10,
            'headers': {}
        }
        
        # Copy relevant headers
        if 'Content-Type' in request.headers:
            request_args['headers']['Content-Type'] = request.headers['Content-Type']
        
        # Add data for POST/PUT requests
        if method in ['POST', 'PUT', 'PATCH'] and request.get_data():
            if request.is_json:
                request_args['json'] = request.get_json()
            else:
                request_args['data'] = request.get_data()
                request_args['headers']['Content-Type'] = request.headers.get('Content-Type', 'application/octet-stream')
        
        # Make the request
        response = requests.request(**request_args)
        
        # Return the response
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Service timeout: {service_url}"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service unavailable: {service_url}"}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with service status"""
    services_status = {}
    
    services = [
        ('Auth Service', AUTH_SERVICE_URL, '/health'),
        ('Cards Service', CARDS_SERVICE_URL, '/health'),
        ('Match Service', MATCH_SERVICE_URL, '/health'),
        ('Player Service', PLAYER_SERVICE_URL, '/health'),
        ('History Service', HISTORY_SERVICE_URL, '/health')
    ]
    
    for service_name, base_url, health_path in services:
        try:
            response = requests.get(f"{base_url}{health_path}", timeout=5)
            services_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "offline",
                "error": str(e)
            }
    
    return jsonify({
        "status": "API Gateway is running",
        "timestamp": datetime.now().isoformat(),
        "services": services_status
    })

# Auth routes
@app.route('/auth/register', methods=['POST'])
def auth_register():
    return forward_request(AUTH_SERVICE_URL, "register", "POST")

@app.route('/auth/login', methods=['POST'])
def auth_login():
    return forward_request(AUTH_SERVICE_URL, "login", "POST")

@app.route('/auth/refresh-token', methods=['POST'])
def auth_refresh_token():
    return forward_request(AUTH_SERVICE_URL, "refresh-token", "POST")

@app.route('/auth/validate-token', methods=['POST'])
def auth_validate_token():
    return forward_request(AUTH_SERVICE_URL, "validate-token", "POST")

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    return forward_request(AUTH_SERVICE_URL, "logout", "POST")

@app.route('/auth/health', methods=['GET'])
def auth_health():
    return forward_request(AUTH_SERVICE_URL, "health", "GET")

# Cards routes
@app.route('/cards/cards', methods=['GET'])
def cards_all():
    return forward_request(CARDS_SERVICE_URL, "cards", "GET")

@app.route('/cards/cards/<card_id>', methods=['GET'])
def cards_specific(card_id):
    return forward_request(CARDS_SERVICE_URL, f"cards/{card_id}", "GET")

@app.route('/cards/suits', methods=['GET'])
def cards_suits():
    return forward_request(CARDS_SERVICE_URL, "suits", "GET")

@app.route('/cards/suits/<suit_name>', methods=['GET'])
def cards_suit(suit_name):
    return forward_request(CARDS_SERVICE_URL, f"suits/{suit_name}", "GET")

@app.route('/cards/special', methods=['GET'])
def cards_special():
    return forward_request(CARDS_SERVICE_URL, "special", "GET")

@app.route('/cards/deck', methods=['POST'])
def cards_deck():
    return forward_request(CARDS_SERVICE_URL, "deck", "POST")

@app.route('/cards/health', methods=['GET'])
def cards_health():
    return forward_request(CARDS_SERVICE_URL, "health", "GET")

# Match routes - CORRETTO: Ora usa /matches/ (plurale) per l'esterno, ma inoltra a "match" (singolare) interno
@app.route('/matches/matches', methods=['POST'])
def match_create():
    return forward_request(MATCH_SERVICE_URL, "match", "POST")

@app.route('/matches/matches', methods=['GET'])
def match_list():
    return forward_request(MATCH_SERVICE_URL, "match", "GET")

@app.route('/matches/matches/<match_id>', methods=['GET'])
def match_get(match_id):
    return forward_request(MATCH_SERVICE_URL, f"match/{match_id}", "GET")

@app.route('/matches/matches/<match_id>/play', methods=['POST'])
def match_play(match_id):
    return forward_request(MATCH_SERVICE_URL, f"match/{match_id}/play", "POST")

@app.route('/matches/matches/<match_id>', methods=['DELETE'])
def match_delete(match_id):
    return forward_request(MATCH_SERVICE_URL, f"match/{match_id}", "DELETE")

@app.route('/matches/health', methods=['GET'])
def match_health():
    return forward_request(MATCH_SERVICE_URL, "health", "GET")

# Player routes
@app.route('/players/<username>', methods=['GET'])
def players_get(username):
    return forward_request(PLAYER_SERVICE_URL, f"players/{username}", "GET")

@app.route('/players/<username>/stats', methods=['GET'])
def players_get_stats(username):
    return forward_request(PLAYER_SERVICE_URL, f"players/{username}/stats", "GET")

@app.route('/players/<username>/stats', methods=['PUT'])
def players_update_stats(username):
    return forward_request(PLAYER_SERVICE_URL, f"players/{username}/stats", "PUT")

@app.route('/players', methods=['GET'])
def players_list():
    return forward_request(PLAYER_SERVICE_URL, "players", "GET")

@app.route('/players/health', methods=['GET'])
def players_health():
    return forward_request(PLAYER_SERVICE_URL, "health", "GET")

# History routes
@app.route('/history/<username>', methods=['GET'])
def history_get(username):
    return forward_request(HISTORY_SERVICE_URL, f"history/{username}", "GET")

@app.route('/history/stats/<username>', methods=['GET'])
def history_stats(username):
    return forward_request(HISTORY_SERVICE_URL, f"stats/{username}", "GET")

@app.route('/history/match', methods=['POST'])
def history_save():
    return forward_request(HISTORY_SERVICE_URL, "history/match", "POST")

@app.route('/history/match/<match_id>', methods=['GET'])
def history_match_details(match_id):
    return forward_request(HISTORY_SERVICE_URL, f"history/match/{match_id}", "GET")

@app.route('/history/match/<match_id>', methods=['DELETE'])
def history_delete_match(match_id):
    return forward_request(HISTORY_SERVICE_URL, f"history/match/{match_id}", "DELETE")

@app.route('/history/health', methods=['GET'])
def history_health():
    return forward_request(HISTORY_SERVICE_URL, "health", "GET")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 API Gateway starting on port 5000...")
    print("📡 Ready to forward requests to microservices")
    print("🔒 JWT authentication enabled")
    print("🌐 CORS enabled for frontend")
    app.run(host='0.0.0.0', port=5000, debug=False)
