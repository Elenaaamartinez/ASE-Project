#!/bin/bash

echo "Starting La Escoba Microservices..."

# Corretto: app.py invece di app_replit.py
python services/auth-service/app.py &
AUTH_PID=$!
echo "Auth Service started (PID: $AUTH_PID) on port 5001"

python services/cards-service/app.py &
CARDS_PID=$!
echo "Cards Service started (PID: $CARDS_PID) on port 5002"

python services/match-service/app.py &
MATCH_PID=$!
echo "Match Service started (PID: $MATCH_PID) on port 5003"

python services/player-service/app.py &
PLAYER_PID=$!
echo "Player Service started (PID: $PLAYER_PID) on port 5004"

python services/history-service/app.py &
HISTORY_PID=$!
echo "History Service started (PID: $HISTORY_PID) on port 5005"

sleep 2

python services/api-gateway/app.py &
GATEWAY_PID=$!
echo "API Gateway started (PID: $GATEWAY_PID) on port 5000"

sleep 1

echo ""
echo "All microservices are starting..."
echo "Frontend will be available on port 5000"
echo ""
echo "Press Ctrl+C to stop all services"

wait
