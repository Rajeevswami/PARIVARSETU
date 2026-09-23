# ParivarSetu → FamilyNexus

Level 1 renames the product without dropping tenant data. API paths stay
under `/api/v1/`. The response envelope is unchanged.

## What changes

- Product name, slug, domain, cache prefix, Celery app name, email From
  address, frontend title, and browser storage keys.
- Postgres role and database **names**, via
  `scripts/migrate_parivarsetu_to_familynexus.sh`. The password is not
  rewritten. The script never `DROP`s a database or role.
- Synthetic `local@placeholder.parivarsetu.app` user emails only. Real
  mailboxes, including `@parivarsetu.app`, are left alone.

## Existing deployment

Run the script **before** recreating containers against the new compose
defaults. Compose interpolates `${DB_USER}` from the root `.env` or the
shell. Django reads `backend/.env`. The healthcheck uses the compose
value, so changing only one of those files makes Postgres look unhealthy.

```bash
./scripts/migrate_parivarsetu_to_familynexus.sh
# restart the stack without deleting the volume
docker compose up -d --build
```

Do not run `docker compose down -v`.

Docker's official Postgres image does not create a `postgres` superuser
when `POSTGRES_USER` is custom. The script connects as the old role to
the maintenance database `postgres`, terminates other sessions, then
`ALTER DATABASE` and `ALTER ROLE`. If both old and new names exist, it
aborts. If only the new name exists, it skips that rename.

`--dry-run` prints planned changes. `--skip-database` rewrites env files
and placeholder emails without connecting to Postgres.

## After the rename

- Restart the Celery worker. The app name is now `familynexus`. The
  default queue remains `celery`.
- Redis keys under the old prefix are cache-only. They miss and refill.
  The script does not flush Redis.
- The frontend copies `parivarsetu_access_token` to
  `familynexus_access_token` and `parivarsetu-theme` to
  `familynexus-theme` once. An existing new key is not overwritten. That
  token key holds the refresh token; the access token stays in memory.

## Fresh install

`docker-compose.yml` and `backend/.env.example` already default to
`familynexus`. CI creates a fresh `familynexus_test` database. No
migration script is required.
