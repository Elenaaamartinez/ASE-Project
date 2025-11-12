# Battle Card Game - Backend Service

A distributed, microservices-based backend for a PvP turn-based card game. Built with Python Flask, Docker, and following REST best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Running Services](#running-services)
- [Testing](#testing)
- [Development](#development)

---

## Quick Start

### Prerequisites

- Docker Engine
- Docker Compose
- Git

### Installation & Execution

\`\`\`bash
# 1. Clone the repository
git clone https://github.com/your-username/battle-card-game.git
cd battle-card-game

# 2. Build and start all services
docker compose up --build

# 3. Verify services are running
curl http://localhost:5000/health

# 4. View logs
docker compose logs -f

# 5. Stop services
docker compose down
\`\`\`

Once running, the API Gateway is available at `http://localhost:5000`.

---

## Architecture

### High-Level Overview

The system follows a **microservices architecture** with the following components:




### Service Responsibilities

| Service | Port | Responsibility |
|---------|------|-----------------|
| **API Gateway** | 5000 | Routes requests, handles authentication, serves as single entry point |
| **Player Service** | 5001 | User registration, authentication, profile management |
| **Card Service** | 5002 | Card catalog, card details, card properties |
| **Match Service** | 5003 | Match creation, gameplay logic, match history, results |
| **Database** | 5432 | Persistent data storage for all services |

### Communication

- **Client ↔ Gateway**: HTTP/REST (exposed to external network)
- **Gateway ↔ Services**: HTTP/REST (internal Docker network)
- **Services ↔ Database**: SQL queries (internal Docker network)

---

## Project Structure

---

## API Documentation

### Base URL

\`\`\`
http://localhost:5000/api
\`\`\`

All API endpoints require authentication (JWT token) except for `/register` and `/login`.

### Available Endpoints

#### Authentication
- `POST /api/auth/register` - Register a new player
- `POST /api/auth/login` - Login and get JWT token

#### Players
- `GET /api/players` - List all players
- `GET /api/players/{id}` - Get player profile
- `GET /api/players/{id}/matches` - Get player match history

#### Cards
- `GET /api/cards` - List all available cards
- `GET /api/cards/{id}` - Get specific card details

#### Matches
- `POST /api/matches` - Create new match
- `GET /api/matches/{id}` - Get match details
- `POST /api/matches/{id}/move` - Submit player move

For complete API specification with request/response examples, see [docs/API.yaml](docs/API.yaml).

---

## Running Services

### Start All Services

\`\`\`bash
docker compose up
\`\`\`

Services will start in the following order:
1. PostgreSQL database (waits for health check)
2. Player Service
3. Card Service
4. Match Service
5. API Gateway (depends on all services)

### View Service Logs

\`\`\`bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api-gateway
docker compose logs -f player-service
\`\`\`

### Stop Services

\`\`\`bash
# Stop but keep containers
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything including volumes
docker compose down -v
\`\`\`

### Rebuild Services

\`\`\`bash
# Rebuild all images
docker compose build

# Rebuild specific service
docker compose build player-service

# Rebuild and restart
docker compose up --build
\`\`\`

---

## Testing

### Unit Tests (In Isolation)

Tests are provided as Postman collections in the `tests/` directory. Each service has its own test collection with:
- Valid input tests (expecting 200 OK)
- Invalid input tests (expecting error responses)
- Edge case tests

To run:

1. **Import collection into Postman**
   - Open Postman
   - File → Import → Select JSON file

2. **Run collection**
   - Select the collection
   - Click "Run collection"
   - Monitor test results

### Integration Tests

Full system tests available via the API Gateway:

\`\`\`bash
# Register a player
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"secure123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"secure123"}'

# Get all cards
curl http://localhost:5000/api/cards

# Create a match
curl -X POST http://localhost:5000/api/matches \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
\`\`\`

---

## Development

### Adding a New Endpoint

1. Define the route in the respective service's `routes.py`
2. Implement handler logic
3. Add tests to the Postman collection
4. Update `docs/API.yaml`
5. Test with `docker compose up`

### Environment Variables

Services use default configurations. To customize, create a `.env` file:

\`\`\`bash
DATABASE_URL=postgresql://user:password@db:5432/cardgame
JWT_SECRET=your-secret-key
FLASK_ENV=development
\`\`\`

### Viewing Database Content

\`\`\`bash
# Access PostgreSQL CLI
docker compose exec db psql -U postgres -d cardgame

# Common queries
\dt                    # List all tables
SELECT * FROM players; # View players
\`\`\`

---

## Requirements

### Runtime
- Python 3.12+
- Flask 3.0.3
- SQLAlchemy 2.0.23
- PostgreSQL 15+

### Development
- Docker Engine
- Docker Compose
- Postman (for testing)

---

## Support

For issues or questions:
- Check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture info
- Review [docs/API.yaml](docs/API.yaml) for API specifications
- See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for troubleshooting

---

## Team

- **Backend Architecture**: Team development

---
