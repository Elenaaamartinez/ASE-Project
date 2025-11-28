# The Functionality that have to be implementet

## 1. Already Implement

- Microservices architecture, 6 separate services
    - Api Gateway : `sevices/api-gateway/`
    - Auth Service (signup/login) : `services/auth-service/` – Missing full OAuth2/JWT
    - Cards Service : `services/cards-service/` – 40 Spanish cards
    - Match Service : `services/match-service/` – Basic “Escoba” logic
    - Player Service : `services/player-service/` – Profiles and stats
    - History Service : `services/history-service/` – Match history
- REST API : All services expose REST endpoints
- docker-compose.yml : File exists but needs adjustments
- README.md : Basic	Exists but could be improved
- docs/ folder : Contains architecture and guides

## 2. Not Implement

#### Security

- HTTPS with self-signed certificates : Each microservce must use HTTPS, not HTTP
- OAuth2 with JWT tokers : We have basic JWT but not full OAuth2
- Input sanitization : Validate and clean akk incomng data
- Encryption of sensitive data : Passwords must be hashed (bcrypt), not stored in plain text
- User-mode containers: Dockerfiles must use a non-root USER
- Static code analysis: Use tools like Bandit(python)
- Dependency analysis : Scan library vulnerabilities
- Vulnerability-free Docker images : Scan imagenes

#### Testing

- Postman unit test : JSON files exist but need to be check and verify
- Locust performance test : `test/locust/locustfile.py` exits, verify it works
- Test valid input (200 OK) : Each endpoint need at least 1 valid test
- Test invalid input (error) : Each endpoint needs at least 1 error test

#### Documentation

- Final PDF report : Must follow the provided template
- OpenAPI specidication : exist at `docs/openapi/openapi.yaml` check it
- Postman collections : They exist in `test/postman/` check it
- Locust files : File exists in `test/locust/` check it
- GitHub Actions YAML : Create CI/CD pipeline
- Step-by-step guide per functionality : Document full API call sequences

#### DataBases (Persistence)

- Real persistence : Currently everything is in-memory
- PostgreSQL/Redis : docker-compose defines DBs but services don’t use them

#### Game Logic

- Full match lifecycle : Missing: end of match, win conditions, etc
- Microservice communication : Auth -> Player works, but Match -> History does not
- Auto-update match history : Match service must save results in History

## 3. Task List sorted by priority

#### HIGH PRIORITY (Red – First delivery)

- Connect services to real databases (PostgreSQL/Redis)
- Implement password hashing (bcrypt)
- Complete game logic (end of match, final score)
- Match Service → History Service integration

#### MEDIUM PRIORITY (Yellow – Final delivery)

- HTTPS for all services (self-signed certs)
- Full OAuth2 (access + refresh tokens)
- Input sanitization for all endpoints
- GitHub Actions for CI/CD
- Complete Postman tests (valid + invalid per endpoint)
- Secure Dockerfiles (non-root users)
- Security analysis (Bandit, Trivy)

#### LOW PRIORITY (Green / Optional)

- Automatic matchmaking
- Ranking system
- Additional features