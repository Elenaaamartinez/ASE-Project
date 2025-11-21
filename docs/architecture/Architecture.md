# System Architecture - La Escoba Card Game

## 1. Group Info

**Project name:** La Escoba - Card Game Backend**Team members:**

- [Elena Martínez Vazquez]
- [Mario Perez Perez]
- [Michele F. P. Sagone]
- [Shahd Amer]

---

## 2. Player Information

So basically, each player's gonna have this info:

### Player Profile

```json
{
  "player_id": "uuid",
  "username": "string (unique)",
  "email": "string (unique)",
  "created_at": "timestamp",
  "profile_picture": "url (optional)",
  "total_score": "integer",
  "level": "integer",
  "matches_played": "integer",
  "matches_won": "integer",
  "matches_lost": "integer",
  "win_rate": "float"
}
```

### Account Credentials

```json
{
  "user_id": "uuid",
  "username": "string",
  "password_hash": "string (bcrypt)",
  "salt": "string",
  "last_login": "timestamp",
  "account_status": "active|suspended|banned"
}
```

### Match History

Players can check out their full match history with stuff like:

- Date and time of the match
- Who they played against
- Result (win/loss)
- Points scored
- Moves they made

---

## 3. Card Collection and Game Rules

### Spanish Deck (40 cards)

#### Suits

1. **Oros (Coins)** (sort value: 4)
2. **Copas (Cups)** (sort value: 3)
3. **Espadas (Swords)** (sort value: 2)
4. **Bastos (Clubs)** (sort value: 1)

#### Card values per suit

- **1-7**: Number cards
- **10**: Sota (Jack)
- **11**: Caballo (Knight)
- **12**: Rey (King)

### Gameplay Mechanics

Each card has two main properties:

#### 1. Numeric Value (for adding up in La Escoba)

- Cards 1-7: value = their number
- Sota (10): value = 8
- Caballo (11): value = 9
- Rey (12): value = 10

#### 2. Ranking (for comparisons)

**Priority: Numeric value > Suit**

**Some examples:**

- 5 of Oros vs 3 of Copas → 5 of Oros wins (5 > 3, pretty straightforward)
- 7 of Oros vs 7 of Copas → 7 of Oros wins (same value, but Oros beats Copas)
- Rey of Bastos vs Sota of Oros → Rey wins (10 > 8)

### Special Cards (Extra points in La Escoba)

- **7 of Oros**: Worth 1 extra point (the most valuable card)
- **7 of Copas**: Worth 1 extra point
- **Most cards captured**: 1 point
- **Most Oros captured**: 1 point
- **Escoba**: Every time you capture all cards on the table = 1 point

---

## 4. Microservices Architecture

### Component Diagram

```ascii
┌─────────────┐
│   Jugador   │
└──────┬──────┘
       │ HTTPS/REST
       ▼
┌─────────────────────┐
│   API Gateway       │  (Kong/Nginx)
│   - Routing         │
│   - Rate limiting   │
│   - SSL/TLS         │
└──────┬──────────────┘
       │
       ├──────────────┬──────────────┬──────────────┬──────────────┐
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Auth    │   │ Player   │   │  Card    │   │  Match   │   │ History  │
│ Service  │   │ Service  │   │ Service  │   │ Service  │   │ Service  │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Auth DB │   │Player DB│   │ Card DB │   │Match DB │   │History  │
│  (PG)   │   │  (PG)   │   │  (PG)   │   │ (Redis) │   │DB (PG)  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## 4. Microservices Architecture

### 4.1. API Gateway
**Responsibility:**  
Acts as the single entry point of the system. It forwards all client requests to the appropriate internal services and handles routing. Future improvements include HTTPS termination and rate-limiting.

**Technology:** Flask-based reverse proxy  
**Port:** `5000` (exposed to users)

---

### 4.2. Authentication Service
**Responsibility:**  
Handles all account-related operations such as user registration, login, and JWT token issuance/validation.

**Database:** PostgreSQL → `users` table  

**Endpoints:**
```bash
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new user |
| POST | `/auth/login` | Authenticate and return JWT |
| GET | `/auth/health` | Service health check |
```

---

### 4.3. Player Service
**Responsibility:**  
Manages player profiles, rankings, statistics, and gameplay achievements.

**Database:** PostgreSQL → `players` and `player_profiles` tables  

**Endpoints:**
```bash
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/players/{username}` | Retrieve player profile |
| PUT | `/players/{username}/stats` | Update stats after a match |
| GET | `/players/health` | Service health check |
```

---

### 4.4. Card Service
**Responsibility:**  
Provides full card deck data and card details for gameplay. Maintains the Spanish 40-card deck.

**Database:** PostgreSQL or static JSON → `cards` table  

**Endpoints:**
```bash
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cards/cards` | Returns all cards in the deck |
| GET | `/cards/cards/{card_id}` | Return a specific card |
| GET | `/cards/health` | Service health check |
```

---

### 4.5. Match Service
**Responsibility:**  
Creates and manages active 1v1 matches and implements La Escoba game rules (hands, table state, scoring, escobas, special cards, etc.).

**Database:** Redis (or in-memory for MVP)  
**Key Structure:** `match:{match_id} → JSON state`

**Endpoints:**
```bash
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/matches/matches` | Create a new match |
| GET | `/matches/matches/{match_id}?player={username}` | Retrieve match state |
| POST | `/matches/matches/{match_id}/play` | Play a card |
```

**Communication with other services:**
- Card Service → fetch deck information
- Player Service → update final score and stats
- History Service → store match results permanently

---

### 4.6. History Service
**Responsibility:**  
Stores completed match data and provides full player match history.

**Database:** PostgreSQL → `matches`, `match_moves`, `match_scores` tables  

**Endpoints:**
```bash
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/history/{username}` | Retrieves player match history |
| POST | `/history/matches` | Save new match result |
| GET | `/history/health` | Service health check |
```
---

## 5. Databases Overview
```bash
| Service | Database | Stored Data |
|--------|----------|-------------|
| Auth Service | PostgreSQL | User accounts |
| Player Service | PostgreSQL | Player profile & statistics |
| Card Service | PostgreSQL / JSON | Spanish card deck |
| Match Service | Redis KV | Active match state |
| History Service | PostgreSQL | Completed match history |
```

---

### Table Definitions

#### Auth Database
```bash
| Table | Description |
|-------|-------------|
| `users` | id, username, email, password_hash, salt, created_at, last_login |
```

#### Player Database
```bash
| Table | Description |
|-------|-------------|
| `players` | id, user_id, total_score, level, matches_played, wins, losses, win_rate |
| `player_profiles` | player_id, profile_picture, bio, preferences |
```

#### Card Database
```bash
| Table | Description |
|-------|-------------|
| `cards` | id, suit, value, numeric_value, image_url, suit_order |
```

#### Match Database
```bash
| Key | Value |
|-----|-------|
| `match:{match_id}` | Full match state (table cards, hands, score, etc.) |
```

#### History Database
```bash
| Table | Description |
|-------|-------------|
| `matches` | id, player1_id, player2_id, winner_id, start_time, end_time |
| `match_moves` | move-by-move log |
| `match_scores` | scoring breakdown |
```

---

## 6. User Flows

### Registration & Login
- 1. Player registers  
- 2. Player logs in and receives JWT  
- 3. Token required to access API endpoints

### Browse Cards

`GET /cards/cards` displays the full Spanish deck

### Play Match

- 1. Create match  
- 2. Players request match state  
- 3. Play cards turn-by-turn  
- 4. When match ends → state sent to History Service  
- 5. Player statistics updated

### View Match History

`GET /history/{username}` returns match results & stats

---

## 7. Deployment

All microservices are launched together using Docker Compose:

```bash
docker compose up --build