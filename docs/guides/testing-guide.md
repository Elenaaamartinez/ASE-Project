# Testing Guide - Escoba Game API

## Prerequisiti
- Docker e Docker Compose installati
- Tutti i servizi in esecuzione (`docker-compose up --build`)
- Strumenti utili: `curl`, `jq` (opzionale)

## Test degli Endpoint

### Health Checks
```bash
# Test API Gateway
curl http://localhost:5000/health

# Test Auth Service
curl http://localhost:5000/auth/health

# Test Cards Service  
curl http://localhost:5000/cards/health

# Test Matches Service
curl http://localhost:5000/matches/health

# Test Player Service
curl http://localhost:5000/player/health

# Test History Service
curl http://localhost:5000/history/health
