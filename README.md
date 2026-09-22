# FamilyNexus

**Connecting Families Through Financial Transparency**

Enterprise SaaS for multi-family financial management — role-based access,
shared ledgers, and joint family financial coordination.

## Tech Stack

| Layer    | Stack |
|----------|-------|
| Backend  | Python 3.13, Django 5, Django REST Framework, PostgreSQL 17, Redis, Celery |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Query |
| Infra    | Docker, Docker Compose, Nginx (reverse proxy, prod) |

## Quick Start

```bash
git clone https://github.com/Rajeevswami/PARIVARSETU.git familynexus && cd familynexus
./scripts/setup.sh
```

- Backend: http://localhost:8000
- API docs: http://localhost:8000/api/v1/docs/
- Frontend: http://localhost:5173

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for manual setup and
production deployment.

## Documentation

- [Rebrand and data migration](docs/REBRAND.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Authentication Guide](docs/AUTHENTICATION.md)
- [Database Documentation](docs/DATABASE.md)
- [API Endpoints Overview](docs/API_ENDPOINTS.md)
- [Expense API Documentation](docs/EXPENSE_API.md)
- [Loan & Borrow/Lend API Documentation](docs/LOAN_API.md)
- [Accounting Documentation](docs/ACCOUNTING.md)
- [Ledger API Documentation](docs/LEDGER_API.md)
- [SaaS core](docs/SAAS.md)
- [Operations](docs/OPERATIONS.md)
- [Assistant](docs/ASSISTANT.md)
- [Launch checks](docs/LAUNCH.md)
- [Security review notes](docs/SECURITY_REVIEW.md)

## Project Status

The ledger, expenses, loans, documents, and administration modules are in
place. FamilyNexus adds billing limits, privacy export, referrals,
onboarding, a family-scoped assistant, and public launch pages. Verified
on sqlite: 275 backend tests passed. Frontend unit tests: 42 passed.
`npx tsc -b` and `npm run lint` exited 0. The Playwright suite is one
public pricing spec and passed against a local Chromium. pgvector is not
enabled on `postgres:17-alpine`; see `docs/ASSISTANT.md`.

## Development Commands

```bash
# Backend
cd backend
black . && isort . && flake8 .
pytest

# Frontend
cd frontend
npm run lint
npm run test
npm run build

# Both, in one shot
./scripts/run-tests.sh
```

## License

Proprietary — all rights reserved.
