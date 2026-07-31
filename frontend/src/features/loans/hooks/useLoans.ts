import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { Loan } from "@/types/loan";

import { loansApi, type CreateLoanPayload, type LoanListParams } from "../api/loansApi";

export function useLoans(params: LoanListParams = {}) {
  return useQuery({ queryKey: ["loans", params], queryFn: () => loansApi.list(params) });
}

export function useLoan(id: string | undefined) {
  return useQuery({
    queryKey: ["loans", id],
    queryFn: () => loansApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useLoanStats(params: LoanListParams = {}) {
  return useQuery({ queryKey: ["loans", "stats", params], queryFn: () => loansApi.stats(params) });
}

export function useCreateLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateLoanPayload) => loansApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loans"] }),
  });
}

export function useCancelLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => loansApi.cancel(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loans"] }),
  });
}

export function useRecordPayment(loanId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      amount: string;
      payment_date: string;
      payment_method: string;
      remarks?: string;
    }) => loansApi.recordPayment(loanId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["loans", loanId] });
      queryClient.invalidateQueries({ queryKey: ["loans"] });
    },
  });
}

export function useLoanTypes() {
  return useQuery({ queryKey: ["loan-types"], queryFn: () => loansApi.listTypes() });
}

export function useCreateLoanType() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) => loansApi.createType(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loan-types"] }),
  });
}

export function useReminders() {
  return useQuery({ queryKey: ["loan-reminders"], queryFn: () => loansApi.listReminders() });
}

export function useCreateReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      loan?: string;
      member: string;
      reminder_type: string;
      title: string;
      message?: string;
      remind_at: string;
    }) => loansApi.createReminder(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loan-reminders"] }),
  });
}

export function useDismissReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => loansApi.dismissReminder(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loan-reminders"] }),
  });
}

export type { Loan };
