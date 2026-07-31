import { api } from "@/api/axios";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type {
  AccountGroup,
  AccountStatement,
  FamilyFinancialSummary,
  FinancialPeriod,
  Journal,
  LedgerAccount,
  TrialBalance,
} from "@/types/ledger";

export interface JournalListParams {
  search?: string;
  status?: string;
  transaction_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface JournalLineInput {
  ledger_account: string;
  entry_type: "debit" | "credit";
  amount: string;
  description?: string;
}

export const ledgerApi = {
  listAccountGroups: () =>
    api.get<ApiResponse<AccountGroup[]>>("/ledger/account-groups/").then((r) => r.data.data),

  listAccounts: (search?: string) =>
    api
      .get<ApiResponse<LedgerAccount[]>>("/ledger/accounts/", { params: { search } })
      .then((r) => r.data.data),
  createAccount: (data: {
    account_code: string;
    account_name: string;
    account_group: string;
    parent_account?: string;
    description?: string;
  }) => api.post<ApiResponse<LedgerAccount>>("/ledger/accounts/", data).then((r) => r.data.data),

  listJournals: (params: JournalListParams = {}) =>
    api.get<PaginatedResponse<Journal>>("/ledger/journals/", { params }).then((r) => r.data),
  getJournal: (id: string) =>
    api.get<ApiResponse<Journal>>(`/ledger/journals/${id}/`).then((r) => r.data.data),
  createJournal: (data: {
    journal_date: string;
    description?: string;
    lines: JournalLineInput[];
  }) => api.post<ApiResponse<Journal>>("/ledger/journals/", data).then((r) => r.data.data),
  postJournal: (id: string) =>
    api.post<ApiResponse<Journal>>(`/ledger/journals/${id}/post_entry/`).then((r) => r.data.data),

  createAdjustment: (data: {
    original_journal?: string;
    journal_date: string;
    reason: string;
    lines: JournalLineInput[];
  }) => api.post("/ledger/adjustments/", data).then((r) => r.data),

  trialBalance: () =>
    api.get<ApiResponse<TrialBalance>>("/ledger/trial-balance/").then((r) => r.data.data),
  accountStatement: (accountId: string, dateFrom?: string, dateTo?: string) =>
    api
      .get<ApiResponse<AccountStatement>>(`/ledger/accounts/${accountId}/statement/`, {
        params: { date_from: dateFrom, date_to: dateTo },
      })
      .then((r) => r.data.data),
  cashBook: () =>
    api.get<ApiResponse<AccountStatement>>("/ledger/cash-book/").then((r) => r.data.data),
  bankBook: () =>
    api.get<ApiResponse<AccountStatement>>("/ledger/bank-book/").then((r) => r.data.data),
  familySummary: () =>
    api
      .get<ApiResponse<FamilyFinancialSummary>>("/ledger/family-summary/")
      .then((r) => r.data.data),

  listFinancialPeriods: () =>
    api.get<ApiResponse<FinancialPeriod[]>>("/ledger/financial-periods/").then((r) => r.data.data),
  closePeriod: (id: string) =>
    api
      .post<ApiResponse<FinancialPeriod>>(`/ledger/financial-periods/${id}/close/`)
      .then((r) => r.data.data),

  journalRegisterExportUrl: () => `${api.defaults.baseURL}/ledger/journal-register/export/`,
};
