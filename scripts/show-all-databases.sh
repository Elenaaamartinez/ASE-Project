#!/bin/bash

echo "🗃️  VISUALIZZAZIONE COMPLETA DATABASE LA ESCOBA"
echo "=============================================="

# Auth Database
echo -e "\n🔐 AUTH DATABASE"
echo "---------------"
docker compose exec auth-db psql -U user -d auth_db -c "SELECT username, email, created_at FROM users;" 2>/dev/null || echo "Tabella users vuota o non esistente"
docker compose exec auth-db psql -U user -d auth_db -c "SELECT session_id, username, created_at FROM sessions;" 2>/dev/null || echo "Tabella sessions vuota o non esistente"

# Player Database
echo -e "\n👥 PLAYER DATABASE"
echo "-----------------"
docker compose exec player-db psql -U user -d player_db -c "SELECT * FROM players;" 2>/dev/null || echo "Tabella players vuota o non esistente"
docker compose exec player-db psql -U user -d player_db -c "SELECT * FROM player_stats;" 2>/dev/null || echo "Tabella player_stats vuota o non esistente"

# Cards Database
echo -e "\n🃏 CARDS DATABASE"
echo "----------------"
docker compose exec cards-db psql -U user -d cards_db -c "SELECT id, name, suit, value, points FROM cards LIMIT 10;" 2>/dev/null || echo "Tabella cards vuota o non esistente"

# History Database
echo -e "\n📊 HISTORY DATABASE"
echo "------------------"
docker compose exec history-db psql -U user -d history_db -c "SELECT match_id, player1, player2, winner, end_time FROM matches;" 2>/dev/null || echo "Tabella matches vuota o non esistente"
docker compose exec history-db psql -U user -d history_db -c "SELECT COUNT(*) as total_moves FROM match_moves;" 2>/dev/null || echo "Tabella match_moves vuota o non esistente"

# Redis (Partite attive)
echo -e "\n🎮 REDIS - PARTITE ATTIVE"
echo "-------------------------"
docker compose exec match-db redis-cli keys "match:*" 2>/dev/null | while read key; do
    echo "Chiave: $key"
    docker compose exec match-db redis-cli get "$key" | python3 -m json.tool 2>/dev/null | head -20
    echo "---"
done || echo "Nessuna partita attiva in Redis"

echo -e "\n✅ Visualizzazione completata!"
