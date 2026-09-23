#!/usr/bin/env bash
# One-shot local setup: env files + first-time container build.
set -euo pipefail

cd "$(dirname "$0")/.."

[ -f backend/.env ] || cp backend/.env.example backend/.env
[ -f frontend/.env ] || cp frontend/.env.example frontend/.env

if grep -q "change-me-to-a-long-random-string" backend/.env; then
  SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
  # portable in-place sed (works on both GNU and BSD sed)
  sed -i.bak "s#change-me-to-a-long-random-string#${SECRET}#" backend/.env && rm -f backend/.env.bak
  echo "Generated SECRET_KEY in backend/.env"
fi

# Compose interpolates DB_* from the shell or a root .env, not backend/.env.
# Export the identity keys so a new install and an unmigrated volume agree.
read_env() {
  local key="$1"
  [ -f backend/.env ] || return 0
  grep -E "^${key}=" backend/.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'"
}
db_name="$(read_env DB_NAME)"
db_user="$(read_env DB_USER)"
db_password="$(read_env DB_PASSWORD)"
[ -n "$db_name" ] && export DB_NAME="$db_name"
[ -n "$db_user" ] && export DB_USER="$db_user"
[ -n "$db_password" ] && export DB_PASSWORD="$db_password"

echo "Building and starting containers..."
docker compose up --build -d

echo "Waiting for the database to be ready..."
until docker compose exec -T db pg_isready -U "${DB_USER:-familynexus}" >/dev/null 2>&1; do
  sleep 1
done

echo "Running migrations..."
docker compose exec -T backend python manage.py migrate

echo "Setup complete."
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/api/v1/docs/"
echo "  Frontend: http://localhost:5173"
