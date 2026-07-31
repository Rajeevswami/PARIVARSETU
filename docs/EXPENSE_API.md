# Expense API Documentation

Full interactive docs: `GET /api/v1/docs/`. This is a human-readable index.

## Design decisions worth knowing

**Ledger integration is a queue, not a ledger.** Every expense create/
update/cancel and every settlement writes a row to `LedgerPostingQueue`
(`apps.expenses.models`). This module does not implement General Ledger
posting — that's the future Ledger Engine module's job — but nothing
bypasses the queue. See `apps.expenses.services.ledger_hook`.

**Default categories are seeded via a signal**, not a field. "Expense
Types" (Personal, Household, Medical, ...) become `ExpenseCategory` rows
automatically when a `Family` is created (`apps/expenses/signals.py`),
watching `families.Family` — zero changes to the families app itself.

**Reports = aggregate endpoints, not a standalone app.** `/expenses/stats/`
returns category/household/member/status breakdowns scoped by whatever
filters are active. The general-purpose `apps.reports`/`apps.dashboard`
apps remain untouched, per this module's boundaries.

**Export is CSV only** (`/expenses/export/`) for this round — Excel/PDF
export are natural follow-ups but out of scope given this module's size;
CSV covers the immediate need and opens in Excel/Sheets directly.

## Categories (`/api/v1/expenses/categories/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/categories/` | List — all family members |
| POST | `/categories/` | Create — family_admin only |
| GET | `/categories/<id>/` | Detail |
| PATCH | `/categories/<id>/` | Update — family_admin only |

## Expenses (`/api/v1/expenses/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/` | List — visibility-filtered for members (private/household/family); filter by `status`, `payment_method`, `paid_by`, `household`, `category`, `date_from`, `date_to`; search `expense_number`/`title`/category name; order by `expense_date`/`amount`/`title`/`created_at` |
| POST | `/` | Create — body includes `split_type` (`equal`/`percentage`/`fixed`/`custom`) and `participants: [{member_id, value?}]` |
| GET | `/<id>/` | Detail — 403 (not 404) if visibility excludes the requester, so "no access" and "doesn't exist" aren't confused |
| PATCH | `/<id>/` | Update — self (own expense) or family_admin |
| DELETE | `/<id>/` | Cancel (soft delete) — family_admin only, members can never delete |
| POST | `/<id>/restore/` | Undo a cancellation — family_admin only |
| POST | `/<id>/attachments/` | Multipart upload; computes a SHA-256 checksum |
| GET | `/<id>/comments/` | List comments |
| POST | `/<id>/comments/add/` | Add a comment (requires a Member profile) |
| POST | `/<id>/settle/` | Record a settlement; rejects amounts that would exceed the participant's share |
| GET | `/stats/` | Aggregate totals — respects the same filters as list |
| GET | `/export/` | CSV download — respects the same filters as list |

`GET /api/v1/expenses/attachments/<attachment_id>/` — records a download
event and returns attachment metadata (separate from the list, which is
nested on the expense detail response).

## Split types

- **equal** — `participants: [{member_id}, ...]`, no `value` needed.
- **percentage** — `participants: [{member_id, value: "60"}, ...]`, must sum to 100.
- **fixed** / **custom** — `participants: [{member_id, value: "200.00"}, ...]`,
  must sum exactly to `amount`. Identical math; the split-type distinction
  is purely about how a frontend presents the entry form.

All rounding remainders (equal/percentage splits that don't divide evenly)
are absorbed by the *last* participant so shares always sum exactly.

## Permissions

| Action | Family Admin | Member |
|---|---|---|
| View allowed expenses | ✅ everything | ✅ per visibility rules |
| Create expense | ✅ | ✅ (must be the payer) |
| Edit expense | ✅ any | ✅ own only |
| Cancel/restore expense | ✅ | ❌ never |
| Manage categories | ✅ | ❌ (read-only) |
| Record settlements | ✅ | — (not exposed to members in this round) |
