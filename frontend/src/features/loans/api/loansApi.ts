import { api } from "@/api/axios";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type { Loan, LoanPayment, LoanStats, LoanType, Reminder } from "@/types/loan";

export interface LoanListParams {
  search?: string;
  status?: string;
  loan_type?: string;
  household?: string;
  date_from?: string;
  date_to?: string;
  ordering?: string;
  page?: number;
}

export interface CreateLoanPayload {
  title: string;
  description?: string;
  borrower: string;
  loan_source: string;
  lender?: string;
  external_lender_name?: string;
  household?: string;
  loan_type?: string;
  principal_amount: string;
  interest_rate?: string;
  interest_type: string;
  loan_date: string;
  due_date?: string;
  allow_overpayment?: boolean;
}

export const loansApi = {
  list: (params: LoanListParams = {}) =>
    api.get<PaginatedResponse<Loan>>("/loans/", { params }).then((r) => r.data),
  get: (id: string) => api.get<ApiResponse<Loan>>(`/loans/${id}/`).then((r) => r.data.data),
  create: (data: CreateLoanPayload) =>
    api.post<ApiResponse<Loan>>("/loans/", data).then((r) => r.data.data),
  update: (id: string, data: Partial<Loan>) =>
    api.patch<ApiResponse<Loan>>(`/loans/${id}/`, data).then((r) => r.data.data),
  cancel: (id: string) => api.delete(`/loans/${id}/`).then((r) => r.data),

  recordPayment: (
    loanId: string,
    data: { amount: string; payment_date: string; payment_method: string; remarks?: string }
  ) =>
    api.post<ApiResponse<LoanPayment>>(`/loans/${loanId}/payments/`, data).then((r) => r.data.data),

  stats: (params: LoanListParams = {}) =>
    api.get<ApiResponse<LoanStats>>("/loans/stats/", { params }).then((r) => r.data.data),

  listTypes: () => api.get<ApiResponse<LoanType[]>>("/loans/types/").then((r) => r.data.data),
  createType: (data: { name: string; description?: string }) =>
    api.post<ApiResponse<LoanType>>("/loans/types/", data).then((r) => r.data.data),

  listReminders: () =>
    api.get<ApiResponse<Reminder[]>>("/loans/reminders/").then((r) => r.data.data),
  createReminder: (data: {
    loan?: string;
    member: string;
    reminder_type: string;
    title: string;
    message?: string;
    remind_at: string;
  }) => api.post<ApiResponse<Reminder>>("/loans/reminders/", data).then((r) => r.data.data),
  dismissReminder: (id: string) => api.post(`/loans/reminders/${id}/dismiss/`).then((r) => r.data),
};
