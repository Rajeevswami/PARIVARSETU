import { api } from "@/api/axios";
import type { PaginatedResponse, ApiResponse } from "@/types/api";
import type { Household } from "@/types/household";

export interface HouseholdListParams {
  search?: string;
  status?: string;
  page?: number;
}

export const householdsApi = {
  list: (params: HouseholdListParams = {}) =>
    api.get<PaginatedResponse<Household>>("/households/", { params }).then((r) => r.data),
  get: (id: string) =>
    api.get<ApiResponse<Household>>(`/households/${id}/`).then((r) => r.data.data),
  create: (data: Partial<Household>) =>
    api.post<ApiResponse<Household>>("/households/", data).then((r) => r.data.data),
  update: (id: string, data: Partial<Household>) =>
    api.patch<ApiResponse<Household>>(`/households/${id}/`, data).then((r) => r.data.data),
  deactivate: (id: string) => api.delete(`/households/${id}/`).then((r) => r.data),
  changeHead: (id: string, memberId: string) =>
    api
      .post<ApiResponse<Household>>(`/households/${id}/change_head/`, { member_id: memberId })
      .then((r) => r.data.data),
};
