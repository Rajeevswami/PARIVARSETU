# Installation Guide

## Prerequisites

- Docker & Docker Compose
- (Optional, for non-Docker local dev) Python 3.13, Node.js 22, PostgreSQL 17, Redis 7

## Quick Start (Docker — recommended)

```bash
git clone <repo-url> parivarsetu && cd parivarsetu
./scripts/setup.sh
```

This copies `.env.example` files, generates a `SECRET_KEY`, builds all
containers, waits for Postgres, and runs migrations.

- Backend: http://localhost:8000
- API docs (Swagger): http://localhost:8000/api/v1/docs/
- Frontend: http://localhost:5173

## Manual Setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# edit backend/.env — set a real SECRET_KEY

docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

## Running Without Docker

**Backend**

```bash
cd backend
python3.13 -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env   # point DB_HOST/REDIS_URL at your local services
python manage.py migrate
python manage.py runserver
```

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Production

```bash
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

Production traffic is fronted by the `nginx` service (port 80), which
routes `/api/`, `/admin/`, `/static/`, `/media/` to Django and everything
else to the frontend container.
