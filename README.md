# La Escoba - Card Game Backend

## Project Lab - Advanced Software Engineering 2025/26

**Building a microservices architecture for the Spanish card game "La Escoba"**

---

## Team Members

- [Elena Martínez Vazquez] - [e.martinezvazquez@studenti.unipi.it]
- [Michele Sagone Francesco Pio] - [m.sagone1@studenti.unipi.it]
- [Student Name 3] - [email@unipi.it]
- [Student Name 4] - [email@unipi.it]

---

## What We're Building

We're creating a microservices-based backend that lets people play the Spanish card game "La Escoba" online. It uses the 40-card Spanish deck and works pretty much like the Italian card game "Scopa" if you're familiar with that.

### Main Features

- **Microservices architecture**: 5 independent services + API Gateway
- **Authentication**: OAuth2 with JWT tokens (for the final version)
- **Matchmaking**: Automatic queue to pair up players
- **Real-time gameplay**: 1v1 matches with full La Escoba game logic
- **Permanent history**: Stores all matches and moves
- **Player stats**: Rankings, scores, win rates

---

## Architecture

```ascii
┌─────────────┐
│   Player    │
└──────┬──────┘
       │ HTTPS/REST
       ▼
┌─────────────────────┐
│   API Gateway       │
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

### The Microservices

1. **Auth Service**: Handles registration, login, and JWT token validation.
2. **Player Service**: Manages profiles, stats, and rankings.
3. **Card Service**: Info about all 40 Spanish cards.
4. **Match Service**: Matchmaking, live matches, game logic.
5. **History Service**: Keeps track of finished matches.

---

## Technologies

!!!!!!!!!!!We haven't decided exactly what we're using yet
- **Backend**: 
- **API Gateway**: 
- **Bases de datos**: 
- **Containerización**: Docker + Docker Compose
- **Testing**: 
- **Seguridad**:

---

## Documentation

All our project documentation is in the `/docs` folder:

- **arquitectura.md**: Detailed architecture description.
- **structurizr.dsl**: Architecture diagram in Structurizr format.
- **SystemContextView.dsl**: High-level system context diagram screenshot.
- **ContainerView.dsl**: Lower-level container diagram showing each part of the project.


### Checking out the Structurizr Diagram

If you want to see the architecture diagram in more detail, we used [https://structurizr.com](https://structurizr.com) to develop this architecture.

1. Go to https://structurizr.com/dsl .
2. Copy the content from `docs/structurizr/workspace.dsl` .
3. Paste it into the online editor.
4. Check out the context and container diagrams

---

## How it works

### Spanish Deck (40 cards)

4 suits: **Coins (Oros), Cups (Copas), Swords (Espadas), Clubs (Bastos)**  
Values: 1-7, Jack (Sota) (10), Knight (Caballo) (11), King (Rey) (12)

### Card Values for Gameplay

- Cards 1-7: worth their number
- Jack (Sota): worth 8
- Knight (Caballo): worth 9
- King (Rey): worth 10

### Scoring

- **Escoba**: - **Escoba**: +1 point (capturing all cards on the table)
- **7 of Coins**: +1 point
- **7 of Cups**: +1 point
- **Most cards captured**: +1 point
- **Most coins captured**: +1 point

First player to reach 15 points wins (or whatever custom target we set).
