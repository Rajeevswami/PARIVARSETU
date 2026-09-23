# Operations

## Secrets

Required runtime values come from the environment. `python manage.py check_secrets` prints missing names, never values. `VAULT_ADDR` and `VAULT_TOKEN` are optional. Settings import does not call Vault and does not fail when those values are empty.

`FIELD_ENCRYPTION_KEY` is a Fernet key. When it is set, family email and SMS provider JSON is encrypted on save. Leave it empty in development. Disk encryption of the Postgres volume is still required.

## Cache and indexes

Production cache is Redis (`CACHES` in base settings). Tests use locmem. `python manage.py review_indexes` lists family-scoped models whose indexes do not start with `family`.

## Tenant isolation

`python manage.py tenant_isolation_audit` exits 0 only when every tenant model has a `family` field or an explicit parent path that reaches one. `billing.Plan` is the platform catalog and is not a leak. A `pre_save` signal stamps child rows from that parent and rejects a cross-family parent. On 2026-09-22 the command against sqlite printed `No unscoped tenant models.`

## Health, metrics, errors

`GET /api/v1/health/` is public and checks the database and cache. `GET /api/v1/metrics/` is staff-only JSON, not a Prometheus text endpoint. Sentry initialises only when `SENTRY_DSN` is set, including the Celery integration when that extra is installed. `send_default_pii` stays false.

## Backup and restore

`python manage.py backup_families --output /var/backups/familynexus` writes one JSON file per active family. That is a logical export, not a substitute for a Postgres volume snapshot. Do not `docker compose down -v`. Restore a snapshot onto a new volume, then run migrations. Redis is a cache and can be rebuilt.

## CI

`.github/workflows/ci.yml` lints and tests the backend against `postgres:17-alpine` (no pgvector) and Redis, and builds the frontend. `.github/workflows/deploy.yml` is manual and only validates the production compose file. It does not push secrets.
