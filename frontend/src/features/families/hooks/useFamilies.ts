import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { Family } from "@/types/family";

import { familiesApi } from "../api/familiesApi";

export function useMyFamily() {
  return useQuery<Family | null>({
    queryKey: ["family", "mine"],
    queryFn: async () => {
      try {
        return await familiesApi.getMine();
      } catch {
        return null;
      }
    },
  });
}

export function useCreateFamily() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Family>) => familiesApi.create(data),
    onSuccess: (family) => {
      queryClient.setQueryData(["family", "mine"], family);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}

export function useUpdateFamily() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Family> }) =>
      familiesApi.update(id, data),
    onSuccess: (family) => queryClient.setQueryData(["family", "mine"], family),
  });
}
