from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:5001"
CARDS_SERVICE_URL = "http://cards-service:5002"
MATCHES_SERVICE_URL = "http://matches-service:5003"
PLAYER_SERVICE_URL = "http://player-service:5004"
HISTORY_SERVICE_URL = "http://history-service:5005"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "API Gateway is running", 
        "services": {
            "auth": AUTH_SERVICE_URL,
            "cards": CARDS_SERVICE_URL,
            "matches": MATCHES_SERVICE_URL,
            "players": PLAYER_SERVICE_URL,
            "history": HISTORY_SERVICE_URL
        }
    })

# Auth routes
@app.route('/auth/register', methods=['POST'])
def auth_register():
    return forward_request(AUTH_SERVICE_URL, "register", "POST")

@app.route('/auth/login', methods=['POST'])
def auth_login():
    return forward_request(AUTH_SERVICE_URL, "login", "POST")

@app.route('/auth/health', methods=['GET'])
def auth_health():
    return forward_request(AUTH_SERVICE_URL, "health", "GET")

# Cards routes
@app.route('/cards/cards', methods=['GET'])
def cards_all():
    return forward_request(CARDS_SERVICE_URL, "cards", "GET")

@app.route('/cards/cards/<int:card_id>', methods=['GET'])
def cards_specific(card_id):
    return forward_request(CARDS_SERVICE_URL, f"cards/{card_id}", "GET")

@app.route('/cards/health', methods=['GET'])
def cards_health():
    return forward_request(CARDS_SERVICE_URL, "health", "GET")

# Matches routes
@app.route('/matches/matches', methods=['POST'])
def matches_create():
    return forward_request(MATCHES_SERVICE_URL, "matches", "POST")

@app.route('/matches/matches/<match_id>', methods=['GET'])
def matches_get(match_id):
    return forward_request(MATCHES_SERVICE_URL, f"matches/{match_id}", "GET")

@app.route('/matches/matches/<match_id>/play', methods=['POST'])
def matches_play(match_id):
    return forward_request(MATCHES_SERVICE_URL, f"matches/{match_id}/play", "POST")

@app.route('/matches/health', methods=['GET'])
def matches_health():
    return forward_request(MATCHES_SERVICE_URL, "health", "GET")

# Player routes
@app.route('/players/<username>', methods=['GET'])
def players_get(username):
    return forward_request(PLAYER_SERVICE_URL, f"players/{username}", "GET")

@app.route('/players/<username>/stats', methods=['PUT'])
def players_update_stats(username):
    return forward_request(PLAYER_SERVICE_URL, f"players/{username}/stats", "PUT")

@app.route('/players/health', methods=['GET'])
def players_health():
    return forward_request(PLAYER_SERVICE_URL, "health", "GET")

# History routes
@app.route('/history/<username>', methods=['GET'])
def history_get(username):
    return forward_request(HISTORY_SERVICE_URL, f"history/{username}", "GET")

@app.route('/history/matches', methods=['POST'])
def history_save():
    return forward_request(HISTORY_SERVICE_URL, "history/matches", "POST")

@app.route('/history/health', methods=['GET'])
def history_health():
    return forward_request(HISTORY_SERVICE_URL, "health", "GET")

def forward_request(service_url, path, method):
    """Forward request to appropriate service"""
    try:
        url = f"{service_url}/{path}"
        
        # Prepare request
        request_args = {
            'method': method,
            'url': url,
            'timeout': 10
        }
        
        # Add data for POST/PUT requests
        if method in ['POST', 'PUT'] and request.get_data():
            try:
                request_args['json'] = request.get_json()
            except:
                request_args['data'] = request.get_data()
        
        response = requests.request(**request_args)
        
        # Return the response
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

if __name__ == '__main__':
    print("🚀 API Gateway starting on port 5000...")
    print("📡 Ready to forward requests to microservices")
    app.run(host='0.0.0.0', port=5000, debug=True)
