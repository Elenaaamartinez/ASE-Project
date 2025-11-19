from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Service URLs
AUTH_SERVICE_URL = "http://auth-service:5001"
CARDS_SERVICE_URL = "http://cards-service:5002"
MATCHES_SERVICE_URL = "http://matches-service:5003"

@app.route('/auth/<path:path>', methods=['GET', 'POST'])
def auth_proxy(path):
    """Route requests to authentication service"""
    try:
        url = f"{AUTH_SERVICE_URL}/{path}"
        
        # Prepare request data based on method
        kwargs = {
            'method': request.method,
            'url': url,
            'headers': {key: value for key, value in request.headers if key != 'Host'},
            'params': request.args
        }
        
        # Only include JSON data for POST requests
        if request.method == 'POST' and request.is_json:
            kwargs['json'] = request.get_json()
            
        response = requests.request(**kwargs)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Auth service unavailable"}), 503

@app.route('/cards/<path:path>', methods=['GET'])
def cards_proxy(path):
    """Route requests to cards service"""
    try:
        url = f"{CARDS_SERVICE_URL}/{path}"
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            params=request.args
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Cards service unavailable"}), 503

@app.route('/matches/<path:path>', methods=['GET', 'POST'])
def matches_proxy(path):
    """Route requests to matches service"""
    try:
        url = f"{MATCHES_SERVICE_URL}/{path}"
        
        # Prepare request data based on method
        kwargs = {
            'method': request.method,
            'url': url,
            'headers': {key: value for key, value in request.headers if key != 'Host'},
            'params': request.args
        }
        
        # Only include JSON data for POST requests
        if request.method == 'POST' and request.is_json:
            kwargs['json'] = request.get_json()
            
        response = requests.request(**kwargs)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Matches service unavailable"}), 503

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "API Gateway is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
