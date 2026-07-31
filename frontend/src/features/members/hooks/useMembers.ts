import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { Member } from "@/types/member";

import { membersApi, type MemberListParams } from "../api/membersApi";

export function useMembers(params: MemberListParams = {}) {
  return useQuery({
    queryKey: ["members", params],
    queryFn: () => membersApi.list(params),
  });
}

export function useMember(id: string | undefined) {
  return useQuery({
    queryKey: ["members", id],
    queryFn: () => membersApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useUpdateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Member> }) =>
      membersApi.update(id, data),
    onSuccess: (member) => {
      queryClient.setQueryData(["members", member.id], member);
      queryClient.invalidateQueries({ queryKey: ["members"] });
    },
  });
}

export function useTransferMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, householdId }: { id: string; householdId: string | null }) =>
      membersApi.transfer(id, householdId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members"] });
      queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });
}

export function useInviteMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      email?: string;
      mobile?: string;
      household?: string;
      relationship?: string;
    }) => membersApi.invite(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invitations"] }),
  });
}

export function useInvitations() {
  return useQuery({
    queryKey: ["invitations"],
    queryFn: () => membersApi.listInvitations(),
  });
}

export function useAcceptInvitation() {
  return useMutation({
    mutationFn: ({
      token,
      first_name,
      password,
    }: {
      token: string;
      first_name?: string;
      password?: string;
    }) => membersApi.acceptInvitation(token, first_name, password),
  });
}

export function useRejectInvitation() {
  return useMutation({
    mutationFn: (token: string) => membersApi.rejectInvitation(token),
  });
}
