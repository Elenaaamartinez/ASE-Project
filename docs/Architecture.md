# System Architecture - La Escoba Card Game

## 1. Group Info

**Project name:** La Escoba - Card Game Backend**Team members:**

- [Elena Martínez Vázquez]
- [Student Name 2]
- [Student Name 3]
- [Student Name 4]

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

### Microservicios

#### 1. API Gateway
**Responsabilidad:**
**Tecnología:**
**Puerto:**

#### 2. Authentication Service
**Responsabilidad:**
**Base de datos:**
**Endpoints:**

#### 3. Player Service
**Responsabilidad:** 
**Base de datos:** 
**Endpoints:**

#### 4. Card Service
**Responsabilidad:** 
**Base de datos:** 
**Endpoints:**

#### 5. Match Service
**Responsabilidad:** 
**Base de datos:** 
**Endpoints:**
**Comunication with other services:**

#### 6. History Service
**Responsabilidad:** 
**Base de datos:** 
**Endpoints:**

### Database

#### Auth Database
**Tablas:**
- `users` (id, username, email, password_hash, salt, created_at, last_login)

#### Player Database
**Tablas:**
- `players` (id, user_id, total_score, level, matches_played, wins, losses, win_rate)
- `player_profiles` (player_id, profile_picture, bio, preferences)

#### Card Database
**Tablas:**
- `cards` (id, suit, value, numeric_value, image_url, suit_order)

#### Match Database
**Estructura:** Key-value store
- `match:{match_id}` → JSON con estado completo de la partida

#### History Database
**Tablas:**
- `matches` (id, player1_id, player2_id, winner_id, start_time, end_time, total_moves)
- `match_moves` (id, match_id, player_id, move_number, action, timestamp)
- `match_scores` (match_id, player_id, points, cards_captured, oros_captured, escobas)

---

## 5. Flujos de Usuario

### Registro y Login
### Ver Cartas
### Jugar Partida
### Ver Historial
## 7. Deployment

El sistema completo se desplegará con Docker Compose:

**Comando de inicio:**
\`\`\`bash
docker compose up
\`\`\`