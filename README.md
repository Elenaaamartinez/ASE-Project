# La Escoba - Card Game Backend

A distributed microservices-based implementation of the Spanish card game "La Escoba" with REST API, Docker deployment, and comprehensive testing.

## What is La Escoba?

La Escoba is a classic Spanish card game played with a 40-card deck (Spanish suited cards: Bastos, Copas, Espadas, Oros). Players try to capture cards from the table by matching cards that sum to 15. Capturing all remaining table cards earns an "escoba" (broom). The winner is determined by a scoring system based on:
- Number of "escobas" (empty table captures)
- Total number of captured cards
- Most coins (Oros)
- Having the 7 of Oros
- Having the 7 of Copas

## Architecture Overview

The backend follows a microservices architecture with the following components:

```
┌─────────────────────────────────────────┐
│          API Gateway (5000)             │
│    (Request routing & JWT validation)   │
└────────────────────┬────────────────────┘
        │            │         │      │         │
        ▼            ▼         ▼      ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ Auth   │ │ Cards  │ │ Match  │ │Player  │ │History │
   │Service │ │Service │ │Service │ │Service │ │Service │
   │(5001)  │ │(5002)  │ │(5003)  │ │(5004)  │ │(5005)  │
   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
      │          │          │         │          │
      ▼          ▼          ▼         ▼          ▼
   Auth DB    Cards DB    Redis    Player DB   History DB
  (postgres) (postgres)           (postgres)  (postgres)
```

### Microservices Description

- **API Gateway**: Central entry point for all client requests. Routes requests to appropriate services and validates JWT tokens.
- **Auth Service**: Handles user registration and login using bcrypt for password hashing and JWT for authentication.
- **Cards Service**: Manages the Spanish card deck (40 cards) with images and game rules.
- **Match Service**: Implements the core La Escoba game logic, manages active matches in Redis.
- **Player Service**: Stores player profiles and statistics.
- **History Service**: Persists completed match records for historical analysis.

## Get Started

### Prerequisites

- Docker and Docker Compose (version 3.8+)
- Git
- Python 3.9+ (for local development)
- PostgreSQL client (optional, for direct DB access)

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ASEProject2
   ```

2. **Build and start all services**
   ```bash
   docker compose up --build
   ```
   
   This will:
   - Generate self-signed SSL certificates for each service
   - Build all microservice Docker images
   - Start all containers (6 services + 5 databases)
   - Initialize databases with schema
   - Output health status for all services

3. **Verify the system is running**
   ```bash
   curl https://localhost:5000/health \
     --cacert ./certs/ca-cert.pem \
     --insecure
   ```

   Or visit in browser (accepting self-signed certificate warning):
   ```
   https://localhost:5000/health
   ```

### Basic API Usage

#### 1. Register a new player
```bash
curl -X POST https://localhost:5000/auth/register \
  --insecure \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "message": "User registered successfully",
  "username": "player1"
}
```

#### 2. Login to get JWT token
```bash
curl -X POST https://localhost:5000/auth/login \
  --insecure \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "player1"
}
```

#### 3. View all cards
```bash
curl https://localhost:5000/cards/cards \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 4. Create a match
```bash
curl -X POST https://localhost:5000/match/match \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player1": "player1",
    "player2": "player2"
  }'
```

Response:
```json
{
  "match_id": "550e8400-e29b-41d4-a716-446655440000",
  "players": ["player1", "player2"],
  "status": "active",
  "message": "Match created successfully"
}
```

#### 5. Get match state
```bash
curl https://localhost:5000/match/match/550e8400-e29b-41d4-a716-446655440000 \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d "?player=player1"
```

#### 6. Play a card
```bash
curl -X POST https://localhost:5000/match/match/550e8400-e29b-41d4-a716-446655440000/play \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player": "player1",
    "card_id": 5
  }'
```

#### 7. View player profile
```bash
curl https://localhost:5000/players/player1 \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 8. View match history
```bash
curl https://localhost:5000/history/player1 \
  --insecure \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Running Tests

#### Postman Unit Tests (requires Postman collection files)
```bash
# Unit tests for individual services
postman_cli collections run ./docs/postman/Auth-Service-Tests.json
postman_cli collections run ./docs/postman/Match-Service-Tests.json
postman_cli collections run ./docs/postman/History-Service-Tests.json
```

#### Integration Tests (with full system running)
```bash
# Same Postman collections can be run against the API Gateway
postman_cli collections run ./docs/postman/Integration-Tests.json
```

#### Performance Tests
```bash
# Run Locust performance tests against the API Gateway
locust -f ./docs/locust/locustfile.py --host https://localhost:5000 \
  --users 100 --spawn-rate 10 --run-time 5m --insecure
```

### Stopping the System

```bash
# Stop all containers
docker compose down

# Stop containers and remove volumes (careful - deletes data)
docker compose down -v
```

## Project Structure

```ascii
ASEProject2/
├── services/
│   ├── api-gateway/           # Main entry point
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── auth-service/          # User authentication
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── cards-service/         # Card management
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── match-service/         # Game logic
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── player-service/        # Player profiles
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── history-service/       # Match records
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
├── databases/
│   ├── init-scripts/
│   │   ├── auth-init.sql        # Auth database schema
│   │   ├── cards-init.sql       # Cards database schema
│   │   ├── player-init.sql      # Player database schema
│   │   └── history-init.sql     # History database schema
│   └── Dockerfile               # PostgreSQL base image
├── certs/                       # SSL certificates (auto-generated)
│   ├── ca-cert.pem
│   ├── ca-key.pem
│   └── {service}-{cert,key}.pem
├── docs/
│   ├── architecture/
│   │   ├── Architecture.md      # Detailed architecture design
│   │   ├── ContainerView.png    # Container diagram
│   │   └── SystemContextView.png
│   ├── openapi/
│   │   └── openapi.yaml         # OpenAPI 3.0 specification
│   ├── postman/
│   │   ├── Auth-Service-Tests.json
│   │   ├── Match-Service-Tests.json
│   │   ├── History-Service-Tests.json
│   │   └── env-dev.json         # Postman environment
│   └── locust/
│       └── locustfile.py        # Performance test scenarios
├── frotend/
|   ├── css
│   │   └── style.css
|   ├── js
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── database-viewer.js
│   │   ├── game.js
│   │   └── utils.js
|   ├── public
│   │   └── images
|   ├── admin.html
|   ├── Dockerfile
|   ├── index.html
|   ├── package.json
|   ├── requirements.txt
│   └── server.py
├── script/
|   ├── clean-db.sh
|   ├── health-check.sh
│   └── postman/
├── test/
|   ├── integration/
|   ├── locust/
│   └── postman/
├── docker-compose.yml         # Service orchestration
└── README.md                  # This file
```

## Security Features

- **HTTPS/TLS**: All inter-service communication uses self-signed certificates
- **JWT Authentication**: Token-based authentication with HS256 algorithm
- **Password Security**: Bcrypt hashing (10 rounds) for secure password storage
- **Non-root Containers**: All services run as non-root user 'appuser'
- **Input Validation**: All endpoints validate and sanitize user inputs
- **Database Isolation**: Each service has its own database instance

## Development

### Adding a new endpoint to a service

1. Update the service's `app.py` with new route handler
2. Forward the route in API Gateway's `app.py`
3. Add tests to the Postman collection
4. Rebuild: `docker compose up --build`

### Viewing logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f auth-service

# Last 100 lines
docker compose logs --tail 100 match-service
```

### Debugging

Enable debug mode by modifying the service's app.py:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # NOT for production
```

## Documentation

- **Architecture**: See `docs/architecture/Architecture.md`
- **OpenAPI Spec**: See `docs/openapi/openapi.yaml` for complete API specification
- **Postman Collections**: See `docs/postman/` for test suites
- **Performance Reports**: See `docs/locust/` for load test results

## Known Limitations

- Frontend is optional and provided as reference only
- SSL certificates are self-signed (warning in browsers/clients is normal)
- Redis persistence is enabled but not replicated (single instance)
- No automatic service discovery (services must be running for health checks to pass)

## Troubleshooting

**Services won't start**
- Check logs: `docker compose logs`
- Ensure ports 5000-5005 are not in use
- Clear volumes: `docker compose down -v` then rebuild

**Certificate errors**
- Certificates are auto-generated in `certs/` folder on first run
- Use `--insecure` flag with curl or accept warnings in browser
- For production: replace with proper signed certificates

**Database connection errors**
- Check database is healthy: `docker compose ps`
- Verify environment variables in docker-compose.yml
- Wait for healthchecks to pass before making requests

**JWT Token expired**
- Get new token: Use login endpoint to refresh
- Check system clock is correct
