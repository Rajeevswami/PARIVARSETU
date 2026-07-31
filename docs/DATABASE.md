# Database Documentation

## Multi-tenancy model

`Family` is the tenant boundary. Every business record (Household, Member,
and every future module's models) carries a `family_id` — either directly
or transitively through a FK to something that has one. Cross-family
access is blocked at the service layer, not just in views (see
`apps.households.services`, `apps.members.services`).

## Core tables (this module)

```
families_family
├── id (UUID, PK)
├── family_code (unique, auto-generated "FAM-XXXXXXXX")
└── ... subscription/locale fields, audit columns

households_household
├── id (UUID, PK)
├── family_id (FK → families_family, CASCADE)
├── household_code (unique per family, not globally — see constraint below)
├── head_of_household_id (FK → members_member, SET_NULL, nullable)
└── ... audit columns

members_member
├── id (UUID, PK)
├── user_id (FK → accounts_user, OneToOne, CASCADE)
├── family_id (FK → families_family, CASCADE)
├── household_id (FK → households_household, SET_NULL, nullable)
├── employee_code (unique per family, auto-generated "MEM-XXXXXXXX")
├── aadhaar_number_ready / pan_number_ready (booleans — see note below)
└── ... audit columns

members_invitation
├── id (UUID, PK)
├── family_id (FK → families_family, CASCADE)
├── household_id (FK → households_household, SET_NULL, nullable)
├── token (unique)
└── CHECK (email IS NOT NULL OR mobile IS NOT NULL)
```

## Circular FK: Household ↔ Member

`Household.head_of_household` points to `Member`; `Member.household`
points back to `Household`. Both are declared with string references
(`"members.Member"` / `"households.Household"`) so Django can resolve
them lazily. Migrations handle this by creating `households_household`
without the FK first, then adding it in a second migration once
`members_member` exists — this is automatic, not something you need to
manage by hand.

## accounts_user.family / household

These started as placeholder `UUIDField`s (Module 3, before Family and
Household existed) and are now real `ForeignKey`s (this module's
migration `accounts.0002_...` / `0003_...`). They're kept nullable and
denormalized on the User row (in addition to the canonical relationship
on `Member`) so permission checks (`request.user.family_id`) stay a
single field lookup rather than a join through `member_profile` on every
request.

## Aadhaar / PAN — why booleans, not the numbers

`aadhaar_number_ready` and `pan_number_ready` are readiness flags, not
storage for the actual government ID numbers. Those are regulated PII
(comparable to a national ID number) and belong in a dedicated,
encrypted KYC/documents module with its own access controls — not in a
general-purpose Member profile table. If/when that module is built,
these flags indicate which members are ready to have their documents
collected there.

## Indexes

- `families_family`: `(status, is_deleted)`, `(family_code)`
- `households_household`: `(family_id, status)`, unique `(family_id, household_code)`
- `members_member`: `(family_id, status)`, `(household_id)`, `(relationship)`, unique `(family_id, employee_code)`
- `members_invitation`: `(family_id, status)`

## Constraints enforcing the module's validation rules

- **Unique family code** — global unique constraint on `family_code`.
- **Unique household code** — unique *per family*
  (`UniqueConstraint(family, household_code)`), not global — two
  unrelated families can each have a "Main House".
- **Member belongs to exactly one family/household** — structural, via
  single (non-nullable family, nullable household) FKs rather than M2M.
- **Cross-family assignment prevention** — enforced in the service layer
  (`transfer_member`, `change_head`, `send_invitation`) by comparing
  `family_id` values before any write; a family admin cannot transfer a
  member into, or invite someone to, a household outside their own
  family. Every one of these checks is covered by a test.

## Expense module tables

```
expenses_category
├── id (UUID, PK)
├── family_id (FK → families_family, CASCADE)
└── UNIQUE (family_id, name) — categories are per-family, not global

expenses_expense
├── id (UUID, PK)
├── expense_number (unique, auto "EXP-XXXXXXXXXX")
├── family_id (FK, CASCADE) / household_id (FK, SET_NULL, nullable)
├── category_id (FK, SET_NULL, nullable)
├── paid_by_id (FK → members_member, PROTECT — can't delete a Member
│   who has expenses on record without reassigning them first)
└── ... amount/status/visibility/audit columns

expenses_participant
├── expense_id (FK, CASCADE) / member_id (FK, CASCADE)
├── share_amount, settled_amount, pending_amount (all Decimal(12,2))
└── UNIQUE (expense_id, member_id) — one row per member per expense

expenses_attachment       — file + SHA-256 checksum + uploader
expenses_comment          — member_id (FK), comment, created_at
expenses_settlement       — one row per settlement event (partial
                             payments are multiple rows, not overwrites)
expenses_ledger_posting_queue
├── expense_id (FK, CASCADE)
├── event_type (expense_created/updated/cancelled, settlement_recorded)
└── status (pending — nothing here ever auto-transitions to "posted"
    yet; that's the future Ledger Engine module's job)
```

### Why `paid_by` is PROTECT, not CASCADE or SET_NULL

Deleting (soft-deleting) a Member shouldn't silently orphan or nullify
the financial history of expenses they paid for — `on_delete=PROTECT`
means the database refuses that operation until the data is explicitly
reassigned, which is the safer default for financial records.

### Settlement math, precisely

`ExpenseParticipant.pending_amount = share_amount - settled_amount`,
recomputed after every settlement (`ExpenseParticipant.recompute()`).
`SettlementService.record_settlement` rejects any settlement where
`already_settled + new_amount > share_amount` — this is what "prevent
duplicate settlements" means in practice: the sum across all settlements
for one participant can never exceed their share.

## Loan / Borrow / Lend module tables

```
loans_type                — per-family loan categories
loans_loan
├── id (UUID, PK), loan_number (unique, auto "LOAN-XXXXXXXXXX")
├── borrower_id (FK → members_member, PROTECT)
├── lender_id (FK → members_member, PROTECT, nullable) — internal loans
├── external_lender_name — external loans (mutually exclusive with lender_id)
├── interest_amount, total_amount, paid_amount, remaining_amount
│   — all computed by the service layer, never set directly by the client
└── allow_overpayment (bool, default False)

loans_installment          — optional installment plan per loan
loans_payment
├── payment_number (unique, auto "PMT-XXXXXXXXXX")
├── interest_paid, principal_paid — interest-first split
└── remaining_balance — snapshot of the loan's balance after this payment

loans_interest_configuration  — reusable per-family default interest settings
loans_reminder                — data records only, no delivery
loans_ledger_posting_queue    — separate from expenses_ledger_posting_queue;
                                 same "queue everything, post nothing yet" pattern

borrow_lend_borrow_transaction
├── borrower_id (FK → members_member, PROTECT)
├── lender_id (FK → members_member, PROTECT, nullable) + external_lender_name
└── settled_amount (running total); remaining_amount is a computed @property

borrow_lend_lend_transaction   — mirror of the above (giver/receiver)

borrow_lend_settlement
├── reference_type ("borrow"/"lend") + reference_id (UUID)
│   — generic association without a GenericForeignKey, consistent with
│   the project's explicit-FK style
└── settled_amount = cumulative total after this event (not per-event)
```

### Interest-first payment application

`PaymentService.record_payment` always pays down any outstanding
interest before principal — standard amortization convention. This is
why `LoanPayment.interest_paid` + `principal_paid` always sum to
`amount`, and why a small payment early in a loan's life can show
`principal_paid: 0.00`.

### Why Loan and Borrow/Lend have separate ledger queues

`apps.loans.LedgerPostingQueue` is distinct from
`apps.expenses.LedgerPostingQueue` — each business domain queues its
own posting requests independently. A future Ledger Engine module
consumes from all of them; this keeps each business app's migration
history self-contained and avoids a premature shared dependency before
that engine actually exists.

## Ledger Engine tables (this module — the "future Ledger Engine" from
## the note above, now built)

```
ledger_account_group          — Assets/Liabilities/Income/Expenses/Equity, per family
ledger_account                — Chart of Accounts (consolidates the spec's
                                 ChartOfAccount + LedgerAccount into one model
                                 — see docs/ACCOUNTING.md)
├── UNIQUE (family_id, account_code)
└── parent_account_id (self-FK, nullable) — hierarchy support

ledger_journal
├── journal_number (unique, auto "JRN-XXXXXXXXXX")
├── status: draft → posted (never edited after posting) → reversed
└── reference_type/reference_id — links back to the source Expense/Loan/etc.

ledger_journal_entry           — one debit or credit line per journal;
                                  a journal's lines must always balance

ledger_entry                   — the POSTED, immutable per-account record;
├── ledger_number (unique, auto "LDG-XXXXXXXXXX")
├── opening_balance / closing_balance — snapshot at that moment
└── never updated or deleted after creation

ledger_account_balance         — current running totals, one row per account,
                                  updated atomically on every posting

ledger_opening_balance         — starting balance per account per FinancialPeriod
ledger_adjustment_entry        — links a correcting journal to what it corrects
ledger_financial_period        — open/closed; postings rejected once closed
ledger_closing_period          — snapshot of balances at period-close time
```

### Consuming apps.expenses / apps.loans without touching them

`apps.ledger.services.queue_consumer.process_pending_postings()` reads
pending rows from `apps.expenses.LedgerPostingQueue` and
`apps.loans.LedgerPostingQueue`, resolves each event to a balanced set
of journal lines (`apps.ledger.services.posting_rules` — pure functions,
unit-tested independent of the DB), posts a real `Journal`, and marks
the source queue row `posted`. Idempotent — safe to re-run; only
`pending` rows are touched.
