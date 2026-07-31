import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ledgerApi, type JournalLineInput, type JournalListParams } from "../api/ledgerApi";

export function useAccountGroups() {
  return useQuery({
    queryKey: ["ledger-account-groups"],
    queryFn: () => ledgerApi.listAccountGroups(),
  });
}

export function useLedgerAccounts(search?: string) {
  return useQuery({
    queryKey: ["ledger-accounts", search],
    queryFn: () => ledgerApi.listAccounts(search),
  });
}

export function useCreateLedgerAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof ledgerApi.createAccount>[0]) =>
      ledgerApi.createAccount(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ledger-accounts"] }),
  });
}

export function useJournals(params: JournalListParams = {}) {
  return useQuery({
    queryKey: ["journals", params],
    queryFn: () => ledgerApi.listJournals(params),
  });
}

export function useJournal(id: string | undefined) {
  return useQuery({
    queryKey: ["journals", id],
    queryFn: () => ledgerApi.getJournal(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateJournal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { journal_date: string; description?: string; lines: JournalLineInput[] }) =>
      ledgerApi.createJournal(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["journals"] }),
  });
}

export function usePostJournal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ledgerApi.postJournal(id),
    onSuccess: (journal) => {
      queryClient.setQueryData(["journals", journal.id], journal);
      queryClient.invalidateQueries({ queryKey: ["journals"] });
      queryClient.invalidateQueries({ queryKey: ["ledger-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["trial-balance"] });
    },
  });
}

export function useCreateAdjustment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof ledgerApi.createAdjustment>[0]) =>
      ledgerApi.createAdjustment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journals"] });
      queryClient.invalidateQueries({ queryKey: ["ledger-accounts"] });
      queryClient.invalidateQueries({ queryKey: ["trial-balance"] });
    },
  });
}

export function useTrialBalance() {
  return useQuery({ queryKey: ["trial-balance"], queryFn: () => ledgerApi.trialBalance() });
}

export function useAccountStatement(
  accountId: string | undefined,
  dateFrom?: string,
  dateTo?: string
) {
  return useQuery({
    queryKey: ["account-statement", accountId, dateFrom, dateTo],
    queryFn: () => ledgerApi.accountStatement(accountId as string, dateFrom, dateTo),
    enabled: Boolean(accountId),
  });
}

export function useCashBook() {
  return useQuery({ queryKey: ["cash-book"], queryFn: () => ledgerApi.cashBook() });
}

export function useBankBook() {
  return useQuery({ queryKey: ["bank-book"], queryFn: () => ledgerApi.bankBook() });
}

export function useFamilySummary() {
  return useQuery({
    queryKey: ["family-financial-summary"],
    queryFn: () => ledgerApi.familySummary(),
  });
}

export function useFinancialPeriods() {
  return useQuery({
    queryKey: ["financial-periods"],
    queryFn: () => ledgerApi.listFinancialPeriods(),
  });
}

export function useClosePeriod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ledgerApi.closePeriod(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["financial-periods"] }),
  });
}
