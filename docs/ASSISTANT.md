# Assistant

Claude tool use lives in `backend/ai_services/`. Views in `apps.assistant` call `answer()` and the channel adapters. They do not call the model API or choose tools.

## Tools

`ledger_summary`, `forecast_expenses`, `detect_anomalies`, `categorize_expense`, `dispute_summary`, `savings_goal`, and `extract_receipt` are family-scoped. Forecasts use a trailing three-month mean. Anomalies are expenses above three times the average. Dispute text is a list of unsettled records, not a legal finding.

The assistant is available when the family is on Premium, when the `ai_copilot` flag is on, or when `FEATURE_AI_COPILOT=true`. An explicit `false` is a kill switch.

Tests inject a scripted transport. `ANTHROPIC_API_KEY` is required only for the live HTTP transport.

## Vectors

Every embedding is stored in `assistant_embedding.embedding_json`. That JSON column is the source of truth until pgvector is present.

Checked on 2026-09-22 in this workspace: there is no running Postgres, no `psql`, and no Docker. The database this process can open is sqlite. `python manage.py sync_pgvector` on that database reports `extension_available: false` and `column_ready: false`. The configured compose image is `postgres:17-alpine`, which does not ship the `vector` extension. CI uses that same Alpine image. The extension is therefore not enabled on the Postgres image this project currently runs.

Enable it without adding a second database:

1. Change the `db` service image in `docker-compose.yml` and `docker-compose.prod.yml` from `postgres:17-alpine` to `pgvector/pgvector:pg17`. Do not run `docker compose down -v`.
2. Recreate only the database container: `docker compose up -d db`.
3. Confirm the package is present: `docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT name FROM pg_available_extensions WHERE name = 'vector';"` The result must be one row, `vector`.
4. Run `python manage.py migrate`. Migration `assistant.0002_pgvector` runs `CREATE EXTENSION IF NOT EXISTS vector` and `ALTER TABLE assistant_embedding ADD COLUMN IF NOT EXISTS embedding vector(1536)` only when that catalog query returns a row. On Alpine or sqlite it no-ops and leaves JSON in place.
5. Copy existing JSON rows: `python manage.py sync_pgvector`. It updates `embedding` from `embedding_json` where `embedding IS NULL`, then prints `synced`.
6. Confirm the column: `\d assistant_embedding` must show `embedding vector(1536)`.

After that, `remember()` writes both stores, and `search()` uses the `<=>` operator. If the column is absent, search stays on cosine similarity over JSON. No separate vector database is added.

## Proactive reports and bots

Celery beat runs `apps.assistant.tasks.send_weekly_family_summaries` every seven days. The task uses the deterministic summary, not a live Claude call. Production compose uses the settings beat schedule.

Telegram and WhatsApp webhooks reject requests when their secrets are empty. A linked chat can record `expense title 40` or `kharcha title 40` through the existing expense service.
