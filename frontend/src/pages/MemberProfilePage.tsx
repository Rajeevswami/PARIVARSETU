import { useParams } from "react-router-dom";

import { MemberProfileForm } from "@/features/members/components/MemberProfileForm";
import { TransferMemberDialog } from "@/features/members/components/TransferMemberDialog";
import { useMember } from "@/features/members/hooks/useMembers";
import { useProfile } from "@/features/auth/hooks/useAuth";

export function MemberProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { data: member, isLoading } = useMember(id);
  const { data: currentUser } = useProfile();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!member) return null;

  const canTransfer = currentUser?.role === "family_admin";

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{member.display_name}</h1>
          <p className="text-sm text-muted-foreground">
            {member.employee_code} · {member.email}
          </p>
          {member.household_name && (
            <p className="text-sm text-muted-foreground">Household: {member.household_name}</p>
          )}
        </div>
        {canTransfer && <TransferMemberDialog member={member} />}
      </div>

      <MemberProfileForm member={member} />
    </div>
  );
}
