# API Usage Examples

## 1. User Registration

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "password123", "email": "player1@email.com"}'
```

## 2. Get All Cards
```bash
curl http://localhost:5000/cards/cards
```

## 3. Get Card Details
```bash
curl http://localhost:5000/cards/cards/15
```

## 4. Create New Match
```bash
curl -X POST http://localhost:5000/matches/matches \
  -H "Content-Type: application/json" \
  -d '{"player1": "player1", "player2": "player2"}'
```

## 5. Get Match State
```bash
curl "http://localhost:5000/matches/matches/MATCH_ID?player=player1"
```
## 6. Play a Card
```bash
curl -X POST http://localhost:5000/matches/matches/MATCH_ID/play \
  -H "Content-Type: application/json" \
  -d '{"player": "player1", "card_id": 15}'
```

## 7. API Gateway Health
```bash
curl http://localhost:5000/health
```

## 8. Auth Service Health
```bash
curl http://localhost:5000/auth/health
```

## 9. Cards Service Health
```bash
curl http://localhost:5000/cards/health
```
## 10. Matches Service Health
```bash
curl http://localhost:5000/matches/health
```

## 11. Register Players
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "mario", "password": "pass123"}'

curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "luigi", "password": "pass123"}'
```

## 12. Create Match
```bash
curl -X POST http://localhost:5000/matches/matches \
  -H "Content-Type: application/json" \
  -d '{"player1": "mario", "player2": "luigi"}'
# Output: {"match_id": "abc-123...", ...}
```

## 13. Play Full Match Example (Mario vs Luigi)

#### Mario checks his hand
```bash
curl "http://localhost:5000/matches/matches/abc-123?player=mario"
```

#### Mario plays a card
```bash
curl -X POST http://localhost:5000/matches/matches/abc-123/play \
  -H "Content-Type: application/json" \
  -d '{"player": "mario", "card_id": 15}'
```

#### Luigi checks his hand
```bash
curl "http://localhost:5000/matches/matches/abc-123?player=luigi"
```

#### Luigi plays a card
```bash
curl -X POST http://localhost:5000/matches/matches/abc-123/play \
  -H "Content-Type: application/json" \
  -d '{"player": "luigi", "card_id": 25}'
```