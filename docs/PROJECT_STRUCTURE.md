# Project Structure

```
parivarsetu/
├── backend/
│   ├── apps/
│   │   ├── common/           # response, exceptions, permissions, pagination, validators, constants, utils
│   │   ├── accounts/         # users, auth (custom User model lands here)
│   │   ├── families/         # multi-family core entity
│   │   ├── households/
│   │   ├── members/
│   │   ├── expenses/
│   │   ├── income/
│   │   ├── loans/
│   │   ├── borrow_lend/
│   │   ├── ledger/
│   │   ├── transactions/
│   │   ├── documents/
│   │   ├── reports/
│   │   ├── notifications/
│   │   ├── dashboard/
│   │   └── audit/
│   ├── config/
│   │   ├── settings/         # base.py, development.py, production.py
│   │   ├── urls.py, wsgi.py, asgi.py, celery.py
│   ├── logs/                 # app.log, error.log, security.log (rotating)
│   ├── media/ static/ templates/
│   ├── requirements/         # base.txt, dev.txt, prod.txt
│   └── manage.py
├── frontend/
│   └── src/
│       ├── app/               # root provider composition
│       ├── components/ui/     # shadcn/ui primitives
│       ├── constants/
│       ├── contexts/
│       ├── features/          # domain-specific code, added per module
│       ├── hooks/
│       ├── layouts/
│       ├── pages/
│       ├── routes/
│       ├── services/
│       ├── store/
│       ├── styles/            # globals.css (Tailwind + CSS variable theme)
│       ├── test/               # vitest setup + tests
│       ├── theme/              # ThemeProvider (dark mode)
│       ├── types/
│       └── lib/                # utils.ts (cn helper)
├── docker/
│   └── postgres/init.sql       # uuid-ossp, pg_trgm extensions
├── nginx/                      # production reverse proxy
├── docs/                       # this guide, installation, development
├── scripts/                    # setup.sh, run-tests.sh
├── .github/workflows/ci.yml
├── docker-compose.yml          # local dev
└── docker-compose.prod.yml     # production
```

## Why apps.common isn't in INSTALLED_APPS

It holds no models — just shared Python utilities (response envelope,
exception handler, permission classes, pagination, validators, constants).
Registering it as a Django app would be misleading; it's imported directly
wherever needed, e.g. `from apps.common.response import success_response`.

## Why every business table will carry family_id / audit columns

Multi-family isolation is enforced at the data layer, not just in views —
every business model will include `family_id`, `created_at`, `updated_at`,
`created_by`, `updated_by`, `is_deleted`, `deleted_at`, `deleted_by` per
the project's data governance requirements (see individual module PRs).
