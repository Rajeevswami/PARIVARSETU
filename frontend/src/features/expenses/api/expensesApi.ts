import { api } from "@/api/axios";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type {
  Expense,
  ExpenseAttachment,
  ExpenseCategory,
  ExpenseComment,
  ExpenseSettlement,
  ExpenseStats,
} from "@/types/expense";

export interface ExpenseListParams {
  search?: string;
  status?: string;
  payment_method?: string;
  paid_by?: string;
  household?: string;
  category?: string;
  date_from?: string;
  date_to?: string;
  ordering?: string;
  page?: number;
}

export interface ExpenseParticipantInput {
  member_id: string;
  value?: string | number;
}

export interface CreateExpensePayload {
  title: string;
  description?: string;
  expense_date: string;
  amount: string;
  currency?: string;
  paid_by: string;
  household?: string;
  category?: string;
  payment_method: string;
  visibility: string;
  reference_number?: string;
  notes?: string;
  split_type: string;
  participants: ExpenseParticipantInput[];
}

export const expensesApi = {
  list: (params: ExpenseListParams = {}) =>
    api.get<PaginatedResponse<Expense>>("/expenses/", { params }).then((r) => r.data),
  get: (id: string) => api.get<ApiResponse<Expense>>(`/expenses/${id}/`).then((r) => r.data.data),
  create: (data: CreateExpensePayload) =>
    api.post<ApiResponse<Expense>>("/expenses/", data).then((r) => r.data.data),
  update: (id: string, data: Partial<Expense>) =>
    api.patch<ApiResponse<Expense>>(`/expenses/${id}/`, data).then((r) => r.data.data),
  cancel: (id: string) => api.delete(`/expenses/${id}/`).then((r) => r.data),
  restore: (id: string) =>
    api.post<ApiResponse<Expense>>(`/expenses/${id}/restore/`).then((r) => r.data.data),

  stats: (params: ExpenseListParams = {}) =>
    api.get<ApiResponse<ExpenseStats>>("/expenses/stats/", { params }).then((r) => r.data.data),
  exportCsvUrl: (params: ExpenseListParams = {}) => {
    const search = new URLSearchParams(params as Record<string, string>).toString();
    return `${api.defaults.baseURL}/expenses/export/${search ? `?${search}` : ""}`;
  },

  listComments: (expenseId: string) =>
    api
      .get<ApiResponse<ExpenseComment[]>>(`/expenses/${expenseId}/comments/`)
      .then((r) => r.data.data),
  addComment: (expenseId: string, comment: string) =>
    api
      .post<ApiResponse<ExpenseComment>>(`/expenses/${expenseId}/comments/add/`, { comment })
      .then((r) => r.data.data),

  uploadAttachment: (expenseId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<ApiResponse<ExpenseAttachment>>(`/expenses/${expenseId}/attachments/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data.data);
  },

  settle: (
    expenseId: string,
    data: { member_id: string; paid_amount: string; settlement_date: string; remarks?: string }
  ) =>
    api
      .post<ApiResponse<ExpenseSettlement>>(`/expenses/${expenseId}/settle/`, data)
      .then((r) => r.data.data),

  listCategories: () =>
    api.get<ApiResponse<ExpenseCategory[]>>("/expenses/categories/").then((r) => r.data.data),
  createCategory: (data: Partial<ExpenseCategory>) =>
    api.post<ApiResponse<ExpenseCategory>>("/expenses/categories/", data).then((r) => r.data.data),
  updateCategory: (id: string, data: Partial<ExpenseCategory>) =>
    api
      .patch<ApiResponse<ExpenseCategory>>(`/expenses/categories/${id}/`, data)
      .then((r) => r.data.data),
};
