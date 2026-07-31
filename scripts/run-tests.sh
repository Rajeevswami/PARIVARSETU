#!/usr/bin/env bash
# Run backend + frontend test suites and linters in one shot.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Backend =="
(cd backend && black --check . && isort --check . && flake8 . && pytest)

echo "== Frontend =="
(cd frontend && npm run lint && npx tsc -b && npm run test)

echo "All checks passed."
