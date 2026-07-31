# Ledger API Documentation

Full interactive docs: `GET /api/v1/docs/`. This is a human-readable index.
See also [Accounting Documentation](ACCOUNTING.md) for the underlying
double-entry design.

## Account Groups & Chart of Accounts (`/api/v1/ledger/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/account-groups/` | The 5 standard groups (read-only, seeded per family) |
| GET | `/accounts/` | List — search by code/name |
| POST | `/accounts/` | Create a custom account — family_admin only |
| GET | `/accounts/<id>/` | Detail, includes `current_balance` |
| PATCH | `/accounts/<id>/` | Update — family_admin only; system accounts' codes are protected |

## Journals

| Method | Path | Notes |
|---|---|---|
| GET | `/journals/` | List — filter by `status`, `transaction_type`, `date_from`, `date_to`; search journal number/reference/description |
| POST | `/journals/` | Create a **manual journal** (draft) — family_admin only. Body: `journal_date`, `description`, `lines: [{ledger_account, entry_type, amount, description}]`. Rejected if debits ≠ credits |
| GET | `/journals/<id>/` | Detail, with all entry lines |
| POST | `/journals/<id>/post_entry/` | Post a draft journal — makes it immutable. Rejects if already posted, unbalanced, or the financial period is closed |

Non-manual journals (expense, loan, borrow, lend, settlement) are
created and posted automatically by the queue consumer — see
[Accounting Documentation](ACCOUNTING.md#integration-how-every-transaction-passes-through-the-ledger-is-real).

## Adjustments

| Method | Path | Notes |
|---|---|---|
| GET | `/adjustments/` | List |
| POST | `/adjustments/` | Create + immediately post a correcting journal — family_admin only. Body: `original_journal` (optional), `journal_date`, `reason`, `lines` |

## Financial Periods

| Method | Path | Notes |
|---|---|---|
| GET | `/financial-periods/` | List |
| POST | `/financial-periods/<id>/close/` | Close a period — family_admin only. Fails if draft journals remain; carries balances forward to the next period |

## Statements

| Method | Path | Notes |
|---|---|---|
| GET | `/trial-balance/` | Every active account's balance; `grand_debit` always equals `grand_credit` |
| GET | `/accounts/<account_id>/statement/` | Generic account statement — optional `date_from`/`date_to` |
| GET | `/cash-book/` | Account statement for account 1001 (Cash) |
| GET | `/bank-book/` | Account statement for account 1002 (Bank) |
| GET | `/family-summary/` | Family/household balance + cash&bank breakdown + income/expense totals |
| GET | `/journal-register/export/` | CSV export of the journal register |

## Permissions

| Action | Family Admin | Member |
|---|---|---|
| View journals/statements | ✅ | ✅ |
| Create manual journal / post / adjust | ✅ | ❌ |
| Create/edit accounts | ✅ | ❌ (read-only) |
| Close a financial period | ✅ | ❌ |
