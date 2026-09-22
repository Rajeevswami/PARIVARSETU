#!/usr/bin/env bash
# Rename an existing ParivarSetu Postgres role/database to FamilyNexus,
# rewrite deployment env files, then rewrite synthetic placeholder emails.
#
# Never drops a database or role. Aborts if both the old and new names exist.
# Run this BEFORE switching a live compose stack onto the new defaults:
# the db healthcheck uses ${DB_USER} from the root .env or the shell, while
# Django reads backend/.env. Docker does not create a "postgres" superuser
# when POSTGRES_USER is custom — connect as the old role to database "postgres".
#
# Redis keys are cache-only. The prefix change is a miss, not data loss; this
# script does not flush Redis. Restart Celery after the app name change. The
# default queue name stays "celery".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OLD_DB="${OLD_DB_NAME:-parivarsetu}"
NEW_DB="${NEW_DB_NAME:-familynexus}"
OLD_USER="${OLD_DB_USER:-parivarsetu}"
NEW_USER="${NEW_DB_USER:-familynexus}"
MAINTENANCE_DB="${MAINTENANCE_DB:-postgres}"
DRY_RUN=0
SKIP_DATABASE=0

usage() {
  echo "Usage: $0 [--dry-run] [--skip-database]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --skip-database) SKIP_DATABASE=1; shift ;;
    *) usage ;;
  esac
done

run_sql() {
  local sql="$1"
  if command -v psql >/dev/null 2>&1 && [[ -n "${PGHOST:-}" || -S /var/run/postgresql/.s.PGSQL.5432 ]]; then
    PGPASSWORD="${PGPASSWORD:-${DB_PASSWORD:-}}" psql -v ON_ERROR_STOP=1 \
      -U "${PGUSER:-$OLD_USER}" -d "$MAINTENANCE_DB" -Atc "$sql"
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose exec -T db true >/dev/null 2>&1; then
    docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$OLD_USER" -d "$MAINTENANCE_DB" -Atc "$sql"
    return
  fi
  return 3
}

rename_database() {
  if [[ "$SKIP_DATABASE" == "1" ]]; then
    echo "Skipping database rename (--skip-database)."
    return
  fi

  local db_list role_list
  if ! db_list="$(run_sql "SELECT datname FROM pg_database WHERE datname IN ('${OLD_DB}', '${NEW_DB}') ORDER BY 1;")"; then
    echo "Could not connect as ${OLD_USER} to maintenance database ${MAINTENANCE_DB}." >&2
    echo "Start the db container, or pass --skip-database and run this SQL yourself:" >&2
    cat <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
 WHERE datname = '${OLD_DB}' AND pid <> pg_backend_pid();
ALTER DATABASE ${OLD_DB} RENAME TO ${NEW_DB};
ALTER ROLE ${OLD_USER} RENAME TO ${NEW_USER};
SQL
    exit 1
  fi
  role_list="$(run_sql "SELECT rolname FROM pg_roles WHERE rolname IN ('${OLD_USER}', '${NEW_USER}') ORDER BY 1;")"

  local has_old_db=0 has_new_db=0 has_old_role=0 has_new_role=0
  [[ "$db_list" == *"$OLD_DB"* ]] && has_old_db=1
  [[ "$db_list" == *"$NEW_DB"* ]] && has_new_db=1
  [[ "$role_list" == *"$OLD_USER"* ]] && has_old_role=1
  [[ "$role_list" == *"$NEW_USER"* ]] && has_new_role=1

  if [[ "$has_old_db" == "1" && "$has_new_db" == "1" ]]; then
    echo "Both databases ${OLD_DB} and ${NEW_DB} exist. Refusing to drop either." >&2
    exit 1
  fi
  if [[ "$has_old_role" == "1" && "$has_new_role" == "1" ]]; then
    echo "Both roles ${OLD_USER} and ${NEW_USER} exist. Refusing to drop either." >&2
    exit 1
  fi
  if [[ "$has_old_db" == "0" && "$has_new_db" == "0" ]]; then
    echo "Neither database name exists. Continuing without a rename."
  elif [[ "$has_old_db" == "0" && "$has_new_db" == "1" ]]; then
    echo "Database ${NEW_DB} already exists. Skipping database rename."
  elif [[ "$DRY_RUN" == "1" ]]; then
    echo "dry-run: would rename database ${OLD_DB} to ${NEW_DB}"
  else
    run_sql "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${OLD_DB}' AND pid <> pg_backend_pid();" >/dev/null
    run_sql "ALTER DATABASE ${OLD_DB} RENAME TO ${NEW_DB};" >/dev/null
    echo "Renamed database ${OLD_DB} to ${NEW_DB}."
  fi

  if [[ "$has_old_role" == "0" && "$has_new_role" == "0" ]]; then
    echo "Neither role exists. Continuing without a role rename."
  elif [[ "$has_old_role" == "0" && "$has_new_role" == "1" ]]; then
    echo "Role ${NEW_USER} already exists. Skipping role rename."
  elif [[ "$DRY_RUN" == "1" ]]; then
    echo "dry-run: would rename role ${OLD_USER} to ${NEW_USER}"
  else
    run_sql "ALTER ROLE ${OLD_USER} RENAME TO ${NEW_USER};" >/dev/null
    echo "Renamed role ${OLD_USER} to ${NEW_USER}. Password unchanged."
  fi
}

rewrite_env_files() {
  python3 - "$ROOT" "$DRY_RUN" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
dry_run = sys.argv[2] == "1"
sys.path.insert(0, str(root / "backend"))
from apps.administration.brand_migration import rewrite_env_file

for relative in ("backend/.env", ".env"):
    path = root / relative
    if not path.is_file():
        print(f"skip missing {relative}")
        continue
    notes = rewrite_env_file(path, dry_run=dry_run)
    print(f"{relative}: {'; '.join(notes) if notes else 'no identity keys to rewrite'}")
PY
}

rewrite_placeholders() {
  local py="python3"
  if [[ -x backend/.venv/bin/python ]]; then
    py="backend/.venv/bin/python"
  fi
  local extra=()
  if [[ "$DRY_RUN" == "1" ]]; then
    extra+=(--dry-run)
  fi
  (
    cd backend
    SECRET_KEY="${SECRET_KEY:-rebrand-placeholder}" "$py" manage.py migrate_placeholder_emails "${extra[@]}"
  )
}

rename_database
rewrite_env_files
rewrite_placeholders

cat <<'NOTE'
Done.
- Do not run "docker compose down -v". That deletes the volume.
- Restart the Celery worker so it picks up the familynexus app name. The queue stays "celery".
- Redis cache keys under the old prefix will miss and refill. Do not flush unless you intend to drop cache.
- Browser refresh tokens and theme keys are copied once by the frontend. Do not clear localStorage first.
NOTE
