# Development Guide

## Workflow

This project is built **module by module**. Each module:

1. Only touches the files it needs to.
2. Ships with tests for what it adds.
3. Passes `scripts/run-tests.sh` before merge.
4. Gets its own commit, e.g. `feat(families): add family CRUD`.

## Backend

```bash
cd backend
black . && isort .          # format
flake8 .                    # lint
pytest                      # tests (uses config.settings.test)
pytest --cov=apps           # tests with coverage
python manage.py makemigrations <app_name>
python manage.py migrate
```

Tests run against a real Postgres database (pytest-django creates/tears
down `test_<DB_NAME>` automatically) — point `DB_HOST`/`DB_USER`/etc. env
vars at a running Postgres + Redis before running `pytest`, or just use
`docker compose up -d db redis` locally.

Business logic lives in **services**, not views. Views/viewsets stay thin —
they parse input, call a service, and return a response via
`apps.common.response`. Keep serializers for validation and shaping only.

## Frontend

```bash
cd frontend
npm run dev
npm run lint
npm run format
npm run test          # vitest run
npm run test:watch
npm run build
```

- Path alias `@/` maps to `src/`.
- Shared UI primitives go in `src/components/ui/` (shadcn/ui convention).
- Feature-specific code (API calls, components, hooks for one domain) goes
  in `src/features/<feature>/`, not scattered across the generic folders.
- Root providers (React Query, Theme, Router) are composed once in
  `src/app/providers.tsx` — add new app-wide context there.

## Git

- `main` — production-ready.
- `develop` — integration branch.
- Feature branches off `develop`: `feat/<module-name>`.
- `pre-commit install` after cloning to enable the hooks in
  `.pre-commit-config.yaml`.

## Adding a New Backend Module

1. App skeleton already exists under `backend/apps/<name>/` — add models,
   serializers, services, views, urls.
2. Register the app's router in `config/urls.py`.
3. `python manage.py makemigrations <name> && python manage.py migrate`.
4. Add tests under `backend/apps/<name>/tests/`.

## Adding a New Frontend Feature

1. Create `src/features/<name>/` with `api.ts`, `components/`, `hooks.ts`.
2. Add the route in `src/routes/index.tsx`.
3. Add a page in `src/pages/` if it needs its own URL.
