export type NormalBalance = "debit" | "credit";
export type JournalStatus = "draft" | "posted" | "reversed";
export type JournalEntryType = "debit" | "credit";

export interface AccountGroup {
  id: string;
  name: string;
  normal_balance: NormalBalance;
  sort_order: number;
}

export interface LedgerAccount {
  id: string;
  account_code: string;
  account_name: string;
  account_group: string;
  account_group_name: string;
  parent_account: string | null;
  description: string;
  status: "active" | "inactive";
  is_system_account: boolean;
  current_balance: string;
  created_at: string;
}

export interface JournalEntryLine {
  id: string;
  ledger_account: string;
  ledger_account_name: string;
  entry_type: JournalEntryType;
  amount: string;
  description: string;
  sequence: number;
}

export interface Journal {
  id: string;
  journal_number: string;
  transaction_type: string;
  reference_type: string;
  reference_id: string;
  journal_date: string;
  description: string;
  status: JournalStatus;
  entries: JournalEntryLine[];
  total_debit: string;
  total_credit: string;
  created_at: string;
  posted_at: string | null;
}

export interface TrialBalanceRow {
  account_code: string;
  account_name: string;
  account_group: string;
  debit_total: string;
  credit_total: string;
  balance: string;
  credit_balance: string;
}

export interface TrialBalance {
  rows: TrialBalanceRow[];
  grand_debit: string;
  grand_credit: string;
}

export interface AccountStatementEntry {
  ledger_number: string;
  transaction_date: string;
  opening_balance: string;
  debit: string;
  credit: string;
  closing_balance: string;
  remarks: string;
  journal_number: string;
}

export interface AccountStatement {
  account_code: string;
  account_name: string;
  entries: AccountStatementEntry[];
}

export interface FinancialPeriod {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: "open" | "closed";
  created_at: string;
}

export interface FamilyFinancialSummary {
  family_balance: string;
  household_balance: string;
  cash_and_bank: Record<string, string>;
  income_expense: { income: string; expense: string };
}
