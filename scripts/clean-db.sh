#!/bin/bash

echo "🧹 Pulizia database auth..."
docker compose exec auth-db psql -U user -d auth_db -c "DELETE FROM sessions;"
docker compose exec auth-db psql -U user -d auth_db -c "DELETE FROM users;"
echo "✅ Database pulito"
