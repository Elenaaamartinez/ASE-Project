# Battle Card Game Backend

Microservices-based backend for a turn-based PvP card battle game.

## Project Overview

This project implements a complete backend system for managing a card battle game where players can:
- Register and authenticate
- View available cards
- Join matches against other players
- Play turn-based card battles
- View match history and statistics

## Architecture

The system follows a microservices architecture with the following components:

### Microservices

I thikn the ones that we have to do it will be the API Gateway, Authentication service, player service, card service, match service, history service and the database manager for the game and for the authentication.

### Databases


## Requirements

##  Quick Start

### Installation

1. Clone the repository:
\`\`\`bash
git clone <https://github.com/Elenaaamartinez/ASE-Project>
cd battle-card-game
\`\`\`

2. Build and start all services:
\`\`\`bash
docker compose up --build
\`\`\`

The API Gateway will be available at `http://localhost:5000`

### Running Tests

#### Unit Tests (Postman/Newman)
\`\`\`bash

# Test individual microservices in isolation

# Integration tests via API Gateway
\`\`\`

#### Performance Tests (Locust)
\`\`\

# Open http://localhost:8089
\`\`\`

## API Documentation

Full OpenAPI specifications are available in `/docs/openapi/`:


### Core Endpoints

This ones were the basic that i have thought of

#### Authentication
- `POST /auth/register` - Register new player
- `POST /auth/login` - Login an old user

#### Cards
- `GET /cards` - List all available cards
- `GET /cards/{id}` - Get specific card details

#### History
- `GET /history` - Get player's match history
- `GET /history/{id}` - Get specific match details

##  Game Rules

### Card Structure
Each card has:
- **Name**: Card identifier
- **Image**: Visual representation
I dont kown yet whta our game will do

### Match Flow
we have to agree in how the game will work

##  Security

we have to agree n the amount of securiity we want to have

##  Architecture Diagrams

Architecture diagrams created with Structurizr are available in `/docs/architecture/`:
- System Context Diagram
- Container Diagram
- Dynamic Diagrams (Registration Flow, Match Flow)

View at: https://structurizr.com/dsl

##  Development

### Project Structure
\`\`\`
battle-card-game/
├── services/
│   └── (Here it will go the diferrent services)
├── tests/
│   └── (Here it will go the diferrent tests)
├── docs/
│   ├── openapi/
│   ├── architecture/
│   └── guides/
├── docker-compose.yml
├── docker-compose.test.yml
└── README.md
\`\`\`

### Adding a New Microservice

1. Create service directory in `/services/`
2. Implement Flask application with REST API
3. Create Dockerfile
4. Add service to `docker-compose.yml`
5. Update API Gateway routing
6. Create OpenAPI specification
7. Write unit tests

##  Team

- [Elena Martínez Vázquez] - e.martinezvazquez@studenti.unipi.it
- [Mario Perez Perez] - name.surname@studenti.unipi.it
- [Team Member 3] - name.surname@studenti.unipi.it
- [Team Member 4] - name.surname@studenti.unipi.it