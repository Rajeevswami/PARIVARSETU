# Accounting Documentation

## Consolidation: ChartOfAccount + LedgerAccount → one model

The spec lists these as two separate models with overlapping fields
(code, name, group, parent, family). In real double-entry accounting
they're the same concept — the chart of accounts *is* the set of
ledger accounts a business posts against. Implementing both would
duplicate one table under two names. `apps.ledger.models.LedgerAccount`
carries every field from both spec sections.

## Default Chart of Accounts (seeded per family)

| Code | Name | Group |
|---|---|---|
| 1001 | Cash | Assets |
| 1002 | Bank | Assets |
| 1003 | UPI | Assets |
| 1004 | Wallet | Assets |
| 1005 | Lend | Assets (money lent out — a receivable) |
| 1006 | Settlement Clearing | Assets |
| 2001 | Loan | Liabilities |
| 2002 | Borrow | Liabilities |
| 3001 | Family Balance | Equity |
| 3002 | Household Balance | Equity |
| 3003 | Adjustment | Equity |
| 4001 | Income | Income |
| 5001 | Expense | Expenses |

Seeded via a signal on `Family` creation (`apps/ledger/signals.py`) —
zero changes to the families app, same pattern as the Expense module's
default categories. An initial open `FinancialPeriod` (current Indian
fiscal year, Apr–Mar) is created at the same time.

## Double-entry rules, enforced where

- **Balanced journal**: `journal_service.create_journal` sums debits and
  credits before any DB write; `posting_service.post_journal`
  re-validates on posting (defense in depth).
- **Reject unbalanced journals**: `ApplicationError(code="unbalanced_journal")`.
- **Never edit posted entries**: `LedgerEntry` rows are created once, at
  posting time, and never updated afterward — there's no update path in
  the codebase. Corrections go through `AdjustmentEntry`.
- **Duplicate posting prevention**: a `Journal` can only move
  draft → posted once; posting an already-posted journal raises
  `ApplicationError(code="duplicate_posting")`.
- **Financial period must be open**: posting checks the journal date
  falls within an `open` `FinancialPeriod` for that family; posting to a
  closed period is rejected.

## How balances are computed

Each `AccountGroup` has a `normal_balance` (debit or credit). For a
debit-normal account (Assets, Expenses), a debit increases the balance
and a credit decreases it; for a credit-normal account (Liabilities,
Income, Equity), it's the reverse. `AccountBalance.current_balance` is
updated atomically on every posting; `LedgerEntry.opening_balance` /
`closing_balance` snapshot that account's balance immediately before
and after that specific entry — so the entry itself is a permanent,
self-contained audit record even if you never look at `AccountBalance`.

## Integration: how "every transaction passes through the Ledger" is real

`apps.expenses.LedgerPostingQueue` and `apps.loans.LedgerPostingQueue`
already existed (built in Modules 5–6 for exactly this). This module
adds a **consumer**, not a producer change:

- `apps.ledger.services.posting_rules` — pure, unit-tested mapping from
  a business event to a balanced set of journal lines (account codes,
  not DB objects — testable without touching the database).
- `apps.ledger.services.queue_consumer.process_pending_postings()` —
  reads pending rows from both queues, resolves account codes to that
  family's actual `LedgerAccount` rows, posts a real `Journal`, and
  marks the queue row `posted` (or leaves it `pending` and logs the
  failure if something's wrong — never silently drops a row).
- Run via `python manage.py process_ledger_queue`, or schedule
  `apps.ledger.tasks.process_pending_ledger_postings` as a Celery Beat
  periodic task for continuous processing.

Zero lines were changed in `apps.expenses` or `apps.loans` to make this
work.

## What "Cash Book" / "Bank Book" / "Ledger Book" actually are

All three (plus a generic "Account Statement") are the same query —
`statement_service.account_statement()` filtered to one account. Cash
Book is that query for account 1001; Bank Book for 1002. Implementing
three separate mechanisms for identical logic would violate the
project's no-duplication convention.

## Closing a period

`closing_service.close_period()`:
1. Refuses to close if any `draft` journal falls within the period
   (`code="draft_journals_remain"`) — everything must be posted or
   explicitly discarded first.
2. Snapshots every account's closing balance into `ClosingPeriod.closing_balances_snapshot`.
3. Creates the next `FinancialPeriod` and an `OpeningBalance` row per
   account, carrying the closing balance forward.
4. Marks the period `closed` — postings to it are rejected from then on.
