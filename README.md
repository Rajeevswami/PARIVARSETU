# ParivarSetu

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
git clone <repo-url> parivarsetu && cd parivarsetu
./scripts/setup.sh
```

- Backend: http://localhost:8000
- API docs: http://localhost:8000/api/v1/docs/
- Frontend: http://localhost:5173

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for manual setup and
production deployment.

## Documentation

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

## Project Status

Built module-by-module. Current state: **Ledger Engine & Accounting
Core** — full double-entry bookkeeping: Chart of Accounts, journals
(manual and auto-posted), immutable ledger entries, running balances,
trial balance, cash/bank books, account statements, financial periods
with carry-forward closing, and adjustment entries. Every Expense/Loan/
Borrow/Lend event is automatically consumed from their existing posting
queues and posted as a real, balanced journal — zero changes to those
modules. 242 backend tests, 40 frontend tests, all passing.

Still not built: Dashboard, Reports UI, Notifications, Document Vault,
Admin Settings, Deployment.

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
