# Development Setup Guide

## 1️. Requirements

- Docker & Docker Compose installed
- Python 3.10+ (only if running microservices manually)
- Git

---

## 2️. Clone the repository

```bash
git clone https://github.com/Elenaaamartinez/ASE-Project
cd MY-ASE-Project
```

## 3. Run the full system via Docker Compose
```bash
docker compose up --build
```
Services available through API Gateway. Examples:
- Auth: http://localhost:5000/auth/health

- Cards: http://localhost:5000/cards/cards

- Matches: http://localhost:5000/matches/health

## 4. Run a service manually (development mode)
```bash
cd services/auth-service
pip install -r requirements.txt
python app.py
```

## 5️. Useful Debug Commands

Stop all services:
```bash
docker compose down
```
Remove all containers + volumes:
```bash
docker compose down -v
```
---