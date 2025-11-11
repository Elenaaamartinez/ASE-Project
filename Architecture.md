# Battle Card Game - Architecture Documentation

## 1. System Overview

### Purpose
A distributed, scalable backend for a turn-based PvP card game utilizing microservices architecture with containerization via Docker and Docker Compose.

### Key Principles
- **Separation of Concerns**: Each service has a single responsibility
- **Stateless Services**: Services don't maintain state between requests
- **Horizontal Scalability**: Services can be scaled independently
- **Clear Communication**: HTTP/REST over internal network

---

## 2. Architectural Pattern: Microservices

\`\`\`
┌─ Monolithic Architecture ──────────┐
│  All functionality in one process   │
│  Harder to scale                    │
│  Single point of failure            │
└─────────────────────────────────────┘

VS

┌─ Microservices Architecture ──────────────────┐
│  Each service independent process              │
│  Scale what you need                           │
│  Services fail independently                   │
└────────────────────────────────────────────────┘
\`\`\`

### Why Microservices?

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| Scalability | Scale entire app | Scale specific service |
| Deployment | Full redeploy | Deploy single service |
| Failure | System down | Service down |
| Development | One codebase | Multiple codebases |
| Technology | Single tech stack | Mix technologies |

---

## 3. Core Components

### 3.1 API Gateway

**Purpose**: Single entry point for all client requests

**Responsibilities**:
- Route requests to appropriate microservices
- Handle authentication/authorization
- Request/response logging
- Error handling and HTTP status codes
- CORS configuration

**Technology**: Flask + Python 3.12

**Port**: 5000 (exposed externally)

**API Routes**:
\`\`\`python
/api/auth/*        → routes to Player Service
/api/players/*     → routes to Player Service
/api/cards/*       → routes to Card Service
/api/matches/*     → routes to Match Service
\`\`\`

**Key Code**:
\`\`\`python
# Gateway receives all requests
@app.route('/api/<service>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_request(service, endpoint):
    # 1. Validate JWT token
    # 2. Route to appropriate microservice
    # 3. Return response to client
\`\`\`

---

### 3.2 Player Service

**Purpose**: Manage user accounts, authentication, and player profiles

**Responsibilities**:
- User registration and login
- Password hashing and verification
- Player profile management
- JWT token generation
- Player statistics tracking

**Technology**: Flask + SQLAlchemy

**Port**: 5001 (internal only)

**Database Tables**:
\`\`\`sql
CREATE TABLE players (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100),
  password_hash VARCHAR(255) NOT NULL,
  total_score INT DEFAULT 0,
  wins INT DEFAULT 0,
  losses INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

**API Endpoints**:
\`\`\`
POST   /register              Register new player
POST   /login                 Login player
GET    /profile/{id}          Get player profile
GET    /stats/{id}            Get player statistics
PUT    /profile/{id}          Update player profile
\`\`\`

---

### 3.3 Card Service

**Purpose**: Manage the card catalog and card properties

**Responsibilities**:
- Provide all available cards
- Return card details and characteristics
- Card images and metadata
- Card rarity and balance information

**Technology**: Flask + SQLAlchemy

**Port**: 5002 (internal only)

**Database Tables**:
\`\`\`sql
CREATE TABLE cards (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  rarity VARCHAR(20),
  image_url VARCHAR(255),
  characteristic_1 INT,              -- e.g., Attack
  characteristic_2 INT,              -- e.g., Defense
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

**API Endpoints**:
\`\`\`
GET    /all                   Get all cards
GET    /card/{id}             Get card details
GET    /characteristics       Get characteristic rules
\`\`\`

**Card Example**:
\`\`\`json
{
  "id": 1,
  "name": "Fire Dragon",
  "description": "A mighty dragon breathing fire",
  "rarity": "legendary",
  "image_url": "https://cdn.example.com/fire-dragon.png",
  "characteristic_1": {"name": "Attack", "value": 95},
  "characteristic_2": {"name": "Defense", "value": 75}
}
\`\`\`

---

### 3.4 Match Service

**Purpose**: Manage game matches, gameplay logic, and match history

**Responsibilities**:
- Create and initialize matches
- Handle player moves during gameplay
- Determine winners based on card comparisons
- Store match results and history
- Calculate points and ratings

**Technology**: Flask + SQLAlchemy

**Port**: 5003 (internal only)

**Database Tables**:
\`\`\`sql
CREATE TABLE matches (
  id SERIAL PRIMARY KEY,
  player_1_id INT NOT NULL REFERENCES players(id),
  player_2_id INT NOT NULL REFERENCES players(id),
  winner_id INT REFERENCES players(id),
  status VARCHAR(20),              -- pending, active, completed
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

CREATE TABLE match_moves (
  id SERIAL PRIMARY KEY,
  match_id INT NOT NULL REFERENCES matches(id),
  player_id INT NOT NULL REFERENCES players(id),
  card_id INT NOT NULL REFERENCES cards(id),
  turn_number INT,
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

**Match Lifecycle**:
\`\`\`
1. PENDING     → Players selected, waiting for opponent
2. ACTIVE      → Game running, players making moves
3. COMPLETED   → Game finished, winner determined
\`\`\`

**API Endpoints**:
\`\`\`
POST   /create                Create new match
GET    /match/{id}            Get match details
POST   /match/{id}/move       Submit player move
GET    /history/{player_id}   Get match history
\`\`\`

---

### 3.5 Database Layer (PostgreSQL)

**Purpose**: Persistent data storage for all services

**Port**: 5432 (internal only, not exposed)

**Database**: `cardgame`

**Schema Overview**:
\`\`\`
┌─────────────────┐
│    players      │
├─────────────────┤
│ id (PK)         │
│ username        │
│ password_hash   │
│ score           │
└─────────────────┘

┌─────────────────┐
│     cards       │
├─────────────────┤
│ id (PK)         │
│ name            │
│ char_1          │
│ char_2          │
└─────────────────┘

┌──────────────────────┐
│     matches          │
├──────────────────────┤
│ id (PK)              │
│ player_1_id (FK)     │
│ player_2_id (FK)     │
│ winner_id (FK)       │
│ status               │
└──────────────────────┘
\`\`\`

---

## 4. Communication Patterns

### 4.1 Client → Gateway

\`\`\`
HTTP Request
    ↓
GET http://localhost:5000/api/players/123
    ↓
Gateway validates JWT token
    ↓
Response returned to client
\`\`\`

### 4.2 Gateway → Microservice

\`\`\`
HTTP Request (internal)
    ↓
GET http://player-service:5001/profile/123
    (uses service name, not localhost)
    ↓
Response returned to gateway
    ↓
Gateway returns to client
\`\`\`

### 4.3 Microservice → Database

\`\`\`
SQLAlchemy ORM Query
    ↓
SELECT * FROM players WHERE id = 123;
    ↓
Database returns result
    ↓
Service processes and returns
\`\`\`

---

## 5. Docker Compose Orchestration

### Service Dependency Graph

\`\`\`yaml
Database
  ↑
  ├─ Player Service
  ├─ Card Service
  ├─ Match Service
       ↑
       API Gateway (depends on all)
\`\`\`

### Startup Sequence

\`\`\`bash
1. docker compose up
   ├─ Start PostgreSQL container
   ├─ Health check: Is DB ready?
   ├─ Start Player Service
   ├─ Start Card Service
   ├─ Start Match Service
   └─ Start API Gateway (waits for dependencies)
\`\`\`

### Container Configuration

\`\`\`yaml
services:
  db:
    image: postgres:15
    ports:
      - "5432:5432"           # Internal only
    environment:
      POSTGRES_DB: cardgame
      POSTGRES_PASSWORD: postgres
    
  api-gateway:
    build: ./api-gateway
    ports:
      - "5000:5000"           # Exposed to clients
    depends_on:
      - player-service
      - card-service
      - match-service
    
  player-service:
    build: ./services/player-service
    ports:
      - "5001:5001"           # Internal network
    depends_on:
      - db
\`\`\`

---

## 6. Data Flow - Gameplay Example

### Scenario: Player registers and plays a match

\`\`\`
Step 1: REGISTRATION
┌──────────┐
│  Client  │ POST /api/auth/register {username, password}
└─────┬────┘
      │
      ▼
┌────────────────────┐
│  API Gateway       │ Route to Player Service
└─────┬──────────────┘
      │
      ▼
┌──────────────────────────┐
│  Player Service          │ Validate, hash password
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│  PostgreSQL              │ INSERT INTO players
└──────────────────────────┘


Step 2: GET CARDS
┌──────────┐
│  Client  │ GET /api/cards {JWT}
└─────┬────┘
      │
      ▼
┌────────────────────┐
│  API Gateway       │ Verify JWT, route to Card Service
└─────┬──────────────┘
      │
      ▼
┌──────────────────────────┐
│  Card Service            │ Query all cards
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│  PostgreSQL              │ SELECT * FROM cards
└──────────────────────────┘


Step 3: CREATE MATCH
┌──────────┐
│  Client  │ POST /api/matches {opponent_id}
└─────┬────┘
      │
      ▼
┌────────────────────┐
│  API Gateway       │ Route to Match Service
└─────┬──────────────┘
      │
      ▼
┌──────────────────────────┐
│  Match Service           │ Create match record
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│  PostgreSQL              │ INSERT INTO matches
└──────────────────────────┘
\`\`\`

---

## 7. Security Architecture

### 7.1 Authentication Flow (JWT)

\`\`\`
1. LOGIN
   POST /api/auth/login {username, password}
   ↓
   Player Service validates credentials
   ↓
   Generate JWT token (expires in 24h)
   ↓
   Return token to client

2. SUBSEQUENT REQUESTS
   GET /api/cards
   Header: Authorization: Bearer <JWT_TOKEN>
   ↓
   Gateway validates token
   ↓
   Extract user ID from token
   ↓
   Route request to service
   ↓
   Service processes with user context
\`\`\`

### 7.2 JWT Token Structure

\`\`\`
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxIiwibmFtZSI6InBsYXllcjEiLCJleHAiOjE3MzE1MDAwMDB9.
signature

Decoded:
{
  "sub": "1",
  "name": "player1",
  "exp": 1731500000
}
\`\`\`

### 7.3 Data Protection

- Passwords: Salted and hashed (bcrypt)
- Database: Internal network only
- API: HTTPS ready (configure with self-signed certs)
- Secrets: Environment variables (not in code)

---

## 8. Scalability & Deployment

### Horizontal Scaling

\`\`\`bash
# Scale Player Service to 3 instances
docker compose up -d --scale player-service=3
\`\`\`

### Load Balancing

In production, add nginx/HAProxy to:
- Distribute requests across service instances
- Health checks
- Circuit breaking

---

## 9. Architectural Anti-patterns Avoided

| Anti-pattern | Impact | Solution |
|--------------|--------|----------|
| Shared Database | Services coupled | Each service owns data |
| No API Gateway | Complex routing | Single gateway entry |
| Synchronous only | Cascading failures | Async where possible |
| No monitoring | Blind to issues | Logging & health checks |

---

## 10. Future Considerations

- Message queue (RabbitMQ) for async communication
- Service mesh (Istio) for advanced routing
- API versioning (v1, v2)
- Caching layer (Redis)
- GraphQL federation
