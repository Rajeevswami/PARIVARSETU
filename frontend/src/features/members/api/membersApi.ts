import { api } from "@/api/axios";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type { Member, MemberInvitation } from "@/types/member";

export interface MemberListParams {
  search?: string;
  household?: string;
  status?: string;
  gender?: string;
  relationship?: string;
  ordering?: string;
  page?: number;
}

export const membersApi = {
  list: (params: MemberListParams = {}) =>
    api.get<PaginatedResponse<Member>>("/members/", { params }).then((r) => r.data),
  get: (id: string) => api.get<ApiResponse<Member>>(`/members/${id}/`).then((r) => r.data.data),
  update: (id: string, data: Partial<Member>) =>
    api.patch<ApiResponse<Member>>(`/members/${id}/`, data).then((r) => r.data.data),
  transfer: (id: string, householdId: string | null) =>
    api
      .post<ApiResponse<Member>>(`/members/${id}/transfer/`, { household_id: householdId })
      .then((r) => r.data.data),

  invite: (data: { email?: string; mobile?: string; household?: string; relationship?: string }) =>
    api.post<ApiResponse<MemberInvitation>>("/members/invitations/", data).then((r) => r.data.data),
  listInvitations: () =>
    api.get<PaginatedResponse<MemberInvitation>>("/members/invitations/").then((r) => r.data),
  acceptInvitation: (token: string, first_name?: string, password?: string) =>
    api
      .post<ApiResponse<Member>>("/members/invitations/accept/", { token, first_name, password })
      .then((r) => r.data),
  rejectInvitation: (token: string) =>
    api.post("/members/invitations/reject/", { token }).then((r) => r.data),
};
