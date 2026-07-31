import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { Expense } from "@/types/expense";

import { expensesApi, type CreateExpensePayload, type ExpenseListParams } from "../api/expensesApi";

export function useExpenses(params: ExpenseListParams = {}) {
  return useQuery({
    queryKey: ["expenses", params],
    queryFn: () => expensesApi.list(params),
  });
}

export function useExpense(id: string | undefined) {
  return useQuery({
    queryKey: ["expenses", id],
    queryFn: () => expensesApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useExpenseStats(params: ExpenseListParams = {}) {
  return useQuery({
    queryKey: ["expenses", "stats", params],
    queryFn: () => expensesApi.stats(params),
  });
}

export function useCreateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateExpensePayload) => expensesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Expense> }) =>
      expensesApi.update(id, data),
    onSuccess: (expense) => {
      queryClient.setQueryData(["expenses", expense.id], expense);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}

export function useCancelExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => expensesApi.cancel(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["expenses"] }),
  });
}

export function useRestoreExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => expensesApi.restore(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["expenses"] }),
  });
}

export function useComments(expenseId: string) {
  return useQuery({
    queryKey: ["expenses", expenseId, "comments"],
    queryFn: () => expensesApi.listComments(expenseId),
  });
}

export function useAddComment(expenseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (comment: string) => expensesApi.addComment(expenseId, comment),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["expenses", expenseId, "comments"] }),
  });
}

export function useUploadAttachment(expenseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => expensesApi.uploadAttachment(expenseId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["expenses", expenseId] }),
  });
}

export function useSettleExpense(expenseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      member_id: string;
      paid_amount: string;
      settlement_date: string;
      remarks?: string;
    }) => expensesApi.settle(expenseId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses", expenseId] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["expense-categories"],
    queryFn: () => expensesApi.listCategories(),
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; color?: string }) =>
      expensesApi.createCategory(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["expense-categories"] }),
  });
}
