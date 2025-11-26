from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:5001"
CARDS_SERVICE_URL = "http://cards-service:5002"
MATCHES_SERVICE_URL = "http://matches-service:5003"
PLAYER_SERVICE_URL = "http://player-service:5004"
HISTORY_SERVICE_URL = "http://history-service:5005"

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
            'params': request.args
        }
        
        # Only add JSON data for POST/PUT requests that have JSON content
        if method in ['POST', 'PUT'] and request.content_type == 'application/json':
            try:
                request_args['json'] = request.get_json()
            except:
                # If JSON parsing fails, continue without JSON data
                pass
        
        response = requests.request(**request_args)
        
        # Return the response from the service
        try:
            return response.json(), response.status_code
        except:
            return response.text, response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/auth/<path:path>', methods=['GET', 'POST'])
def auth_proxy(path):
    """Route requests to authentication service"""
    return make_request(AUTH_SERVICE_URL, path, request.method)

@app.route('/cards/<path:path>', methods=['GET'])
def cards_proxy(path):
    """Route requests to cards service"""
    return make_request(CARDS_SERVICE_URL, path, request.method)

@app.route('/matches/<path:path>', methods=['GET', 'POST'])
def matches_proxy(path):
    """Route requests to matches service"""
    return make_request(MATCHES_SERVICE_URL, path, request.method)

@app.route('/players/<path:path>', methods=['GET', 'PUT'])
def players_proxy(path):
    """Route requests to player service"""
    return make_request(PLAYER_SERVICE_URL, path, request.method)

@app.route('/history/<path:path>', methods=['GET', 'POST'])
def history_proxy(path):
    """Route requests to history service"""
    return make_request(HISTORY_SERVICE_URL, path, request.method)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "API Gateway is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
