import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { Household } from "@/types/household";

import { householdsApi, type HouseholdListParams } from "../api/householdsApi";

export function useHouseholds(params: HouseholdListParams = {}) {
  return useQuery({
    queryKey: ["households", params],
    queryFn: () => householdsApi.list(params),
  });
}

export function useHousehold(id: string | undefined) {
  return useQuery({
    queryKey: ["households", id],
    queryFn: () => householdsApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateHousehold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Household>) => householdsApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["households"] }),
  });
}

export function useUpdateHousehold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Household> }) =>
      householdsApi.update(id, data),
    onSuccess: (household) => {
      queryClient.setQueryData(["households", household.id], household);
      queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });
}

export function useDeactivateHousehold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => householdsApi.deactivate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["households"] }),
  });
}

export function useChangeHead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ householdId, memberId }: { householdId: string; memberId: string }) =>
      householdsApi.changeHead(householdId, memberId),
    onSuccess: (household) => {
      queryClient.setQueryData(["households", household.id], household);
      queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });
}
