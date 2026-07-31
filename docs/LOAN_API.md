# Loan & Borrow/Lend API Documentation

Full interactive docs: `GET /api/v1/docs/`. This is a human-readable index.

## Design decisions worth knowing

**Separate ledger queue from the Expense module's.** `apps.loans` has
its own `LedgerPostingQueue` (distinct table from
`apps.expenses.LedgerPostingQueue`) — each business domain queues its
own posting requests; nothing bypasses it, but this module doesn't
implement actual General Ledger posting (that's the future Ledger
Engine module's job, explicitly out of scope this round).

**Reminders are data records only.** No delivery mechanism — a future
Notifications module would read pending reminders and send them. This
module creates/lists/dismisses reminder records, full stop.

**External parties, not a contact system.** `lender` (Loan),
`lender`/`receiver` (Borrow/Lend) are nullable FKs to `Member` for
internal parties, plus a plain `external_*_name` text field for
external ones. No separate contact-management model.

**Interest is annual-rate, 365-day-year based.** `interest_rate` is
always an annual percentage. Simple interest: `P × R × (days/365)`.
Compound interest additionally takes a compounding frequency
(monthly/quarterly/annually). See `apps.loans.services.interest` — pure,
independently unit-tested functions.

**Loans use `LoanPayment` (interest/principal breakdown); Borrow/Lend
use the generic `Settlement` model** (reference_type + reference_id,
covering both transaction types) — Borrow/Lend carry no interest, so
they don't need Loan's richer payment mechanism.

## Loans (`/api/v1/loans/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/` | List — members see only loans they're a party to (borrower or lender); filter by `status`, `loan_type`, `household`, `borrower`, `lender`, `date_from`, `date_to`; search loan number/title/party names; order by `loan_date`/`principal_amount`/`total_amount`/`title` |
| POST | `/` | Create — `loan_source: internal` requires `lender` (a Member); `external` requires `external_lender_name`. Interest is calculated automatically from `principal_amount`, `interest_rate`, `interest_type`, `loan_date`, `due_date` |
| GET | `/<id>/` | Detail — 403 (not 404) if the requester isn't a party and isn't admin |
| PATCH | `/<id>/` | Update — self (own draft) or family_admin |
| DELETE | `/<id>/` | Cancel (soft delete) — family_admin only |
| POST | `/<id>/restore/` | Undo a cancellation — family_admin only |
| POST | `/<id>/payments/` | Record a payment — interest-first split; rejects amounts over the remaining balance unless the loan has `allow_overpayment: true` |
| GET | `/stats/` | Aggregate totals by status/type, plus outstanding total |
| GET | `/export/` | CSV download |
| GET/POST | `/types/` | Loan type CRUD (family_admin creates) |
| GET/POST | `/reminders/` | Reminder CRUD (data only, no delivery) |
| POST | `/reminders/<id>/dismiss/` | Mark a reminder dismissed |
| GET/POST | `/interest-configurations/` | Reusable default interest settings per family/loan-type |

## Borrow/Lend (`/api/v1/borrow-lend/`)

| Method | Path | Notes |
|---|---|---|
| GET/POST | `/borrow/` | BorrowTransaction list/create — borrower always a Member; lender is a Member OR `external_lender_name` |
| GET | `/borrow/<id>/` | Detail — 403 if not a party and not admin |
| GET/POST | `/lend/` | LendTransaction list/create — giver always a Member; receiver is a Member OR `external_receiver_name` |
| GET | `/lend/<id>/` | Detail |
| POST | `/settlements/` | Body: `reference_type` (`borrow`/`lend`), `reference_id`, `member_id`, `amount`, `settlement_date`. Rejects settlements that would exceed the transaction's total amount (no duplicate/over-settlement) |

## Interest calculation reference

```python
# Simple: I = P × R × T  (T = days/365)
# Compound: A = P × (1 + R/n)^(nT) - P  (n = periods/year)
```

Both are pure functions in `apps.loans.services.interest` — no DB
access, fully unit-tested independent of the API.
