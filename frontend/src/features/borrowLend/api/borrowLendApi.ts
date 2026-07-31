import { api } from "@/api/axios";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type { BorrowTransaction, LendTransaction, Settlement } from "@/types/borrowLend";

export interface TransactionListParams {
  search?: string;
  status?: string;
  household?: string;
  ordering?: string;
  page?: number;
}

export const borrowLendApi = {
  listBorrow: (params: TransactionListParams = {}) =>
    api
      .get<PaginatedResponse<BorrowTransaction>>("/borrow-lend/borrow/", { params })
      .then((r) => r.data),
  getBorrow: (id: string) =>
    api.get<ApiResponse<BorrowTransaction>>(`/borrow-lend/borrow/${id}/`).then((r) => r.data.data),
  createBorrow: (data: {
    borrower: string;
    lender?: string;
    external_lender_name?: string;
    household?: string;
    amount: string;
    date: string;
    reason?: string;
    payment_method: string;
  }) =>
    api.post<ApiResponse<BorrowTransaction>>("/borrow-lend/borrow/", data).then((r) => r.data.data),

  listLend: (params: TransactionListParams = {}) =>
    api
      .get<PaginatedResponse<LendTransaction>>("/borrow-lend/lend/", { params })
      .then((r) => r.data),
  getLend: (id: string) =>
    api.get<ApiResponse<LendTransaction>>(`/borrow-lend/lend/${id}/`).then((r) => r.data.data),
  createLend: (data: {
    giver: string;
    receiver?: string;
    external_receiver_name?: string;
    household?: string;
    amount: string;
    date: string;
    reason?: string;
    payment_method: string;
  }) => api.post<ApiResponse<LendTransaction>>("/borrow-lend/lend/", data).then((r) => r.data.data),

  recordSettlement: (data: {
    reference_type: "borrow" | "lend";
    reference_id: string;
    member_id: string;
    amount: string;
    settlement_date: string;
    remarks?: string;
  }) =>
    api.post<ApiResponse<Settlement>>("/borrow-lend/settlements/", data).then((r) => r.data.data),
};
