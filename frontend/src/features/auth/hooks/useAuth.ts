import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { tokenStorage } from "@/lib/tokenStorage";
import type { User } from "@/types/user";

import { authApi } from "../api/authApi";

const PROFILE_QUERY_KEY = ["profile"] as const;

export function useProfile() {
  return useQuery<User>({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: authApi.getProfile,
    retry: false,
    enabled: Boolean(tokenStorage.getAccessToken() || tokenStorage.getRefreshToken()),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ identifier, password }: { identifier: string; password: string }) =>
      authApi.login(identifier, password),
    onSuccess: (data) => {
      tokenStorage.setAccessToken(data.tokens.access);
      tokenStorage.setRefreshToken(data.tokens.refresh);
      queryClient.setQueryData(PROFILE_QUERY_KEY, data.user);
      navigate("/");
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: () => {
      const refresh = tokenStorage.getRefreshToken();
      if (!refresh) return Promise.resolve(null);
      return authApi.logout(refresh);
    },
    onSettled: () => {
      tokenStorage.clear();
      queryClient.setQueryData(PROFILE_QUERY_KEY, null);
      queryClient.clear();
      navigate("/login");
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (identifier: string) => authApi.forgotPassword(identifier),
  });
}

export function useResetPassword() {
  const navigate = useNavigate();
  return useMutation({
    mutationFn: ({
      token,
      newPassword,
      confirmPassword,
    }: {
      token: string;
      newPassword: string;
      confirmPassword: string;
    }) => authApi.resetPassword(token, newPassword, confirmPassword),
    onSuccess: () => navigate("/login"),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: ({
      oldPassword,
      newPassword,
      confirmPassword,
    }: {
      oldPassword: string;
      newPassword: string;
      confirmPassword: string;
    }) => authApi.changePassword(oldPassword, newPassword, confirmPassword),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<User>) => authApi.updateProfile(data),
    onSuccess: (user) => queryClient.setQueryData(PROFILE_QUERY_KEY, user),
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => authApi.uploadAvatar(file),
    onSuccess: (user) => queryClient.setQueryData(PROFILE_QUERY_KEY, user),
  });
}
