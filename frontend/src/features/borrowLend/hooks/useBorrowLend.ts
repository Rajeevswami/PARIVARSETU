import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { borrowLendApi, type TransactionListParams } from "../api/borrowLendApi";

export function useBorrowTransactions(params: TransactionListParams = {}) {
  return useQuery({
    queryKey: ["borrow", params],
    queryFn: () => borrowLendApi.listBorrow(params),
  });
}

export function useBorrowTransaction(id: string | undefined) {
  return useQuery({
    queryKey: ["borrow", id],
    queryFn: () => borrowLendApi.getBorrow(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateBorrow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof borrowLendApi.createBorrow>[0]) =>
      borrowLendApi.createBorrow(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["borrow"] }),
  });
}

export function useLendTransactions(params: TransactionListParams = {}) {
  return useQuery({ queryKey: ["lend", params], queryFn: () => borrowLendApi.listLend(params) });
}

export function useLendTransaction(id: string | undefined) {
  return useQuery({
    queryKey: ["lend", id],
    queryFn: () => borrowLendApi.getLend(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateLend() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof borrowLendApi.createLend>[0]) =>
      borrowLendApi.createLend(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lend"] }),
  });
}

export function useRecordSettlement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof borrowLendApi.recordSettlement>[0]) =>
      borrowLendApi.recordSettlement(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["borrow"] });
      queryClient.invalidateQueries({ queryKey: ["lend"] });
    },
  });
}
