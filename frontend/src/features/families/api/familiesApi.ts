import { api } from "@/api/axios";
import type { ApiResponse } from "@/types/api";
import type { Family } from "@/types/family";

export const familiesApi = {
  getMine: () => api.get<ApiResponse<Family>>("/families/mine/").then((r) => r.data.data),
  create: (data: Partial<Family>) =>
    api.post<ApiResponse<Family>>("/families/", data).then((r) => r.data.data),
  update: (id: string, data: Partial<Family>) =>
    api.patch<ApiResponse<Family>>(`/families/${id}/`, data).then((r) => r.data.data),
};
