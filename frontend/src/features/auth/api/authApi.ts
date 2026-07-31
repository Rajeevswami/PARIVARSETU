import { api } from "@/api/axios";
import type { ApiResponse } from "@/types/api";
import type { AuthTokens, User } from "@/types/user";

interface LoginResponseData {
  user: User;
  tokens: AuthTokens;
}

export const authApi = {
  login: (identifier: string, password: string) =>
    api
      .post<ApiResponse<LoginResponseData>>("/auth/login/", { identifier, password })
      .then((r) => r.data.data),

  logout: (refresh: string) => api.post("/auth/logout/", { refresh }).then((r) => r.data),

  logoutAllDevices: () => api.post("/auth/logout-all/").then((r) => r.data),

  forgotPassword: (identifier: string) =>
    api.post<ApiResponse<null>>("/auth/forgot-password/", { identifier }).then((r) => r.data),

  resetPassword: (token: string, new_password: string, confirm_password: string) =>
    api
      .post<ApiResponse<null>>("/auth/reset-password/", { token, new_password, confirm_password })
      .then((r) => r.data),

  changePassword: (old_password: string, new_password: string, confirm_password: string) =>
    api
      .post<ApiResponse<null>>("/auth/change-password/", {
        old_password,
        new_password,
        confirm_password,
      })
      .then((r) => r.data),

  getProfile: () => api.get<ApiResponse<User>>("/auth/profile/").then((r) => r.data.data),

  updateProfile: (data: Partial<User>) =>
    api.patch<ApiResponse<User>>("/auth/profile/", data).then((r) => r.data.data),

  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append("profile_photo", file);
    return api
      .post<ApiResponse<User>>("/auth/profile/avatar/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data.data);
  },

  getLoginHistory: () => api.get("/auth/login-history/").then((r) => r.data),
};
