import { useState } from "react";
import { useParams } from "react-router-dom";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ChangeHeadDialog } from "@/features/households/components/ChangeHeadDialog";
import { HouseholdForm } from "@/features/households/components/HouseholdForm";
import { useDeactivateHousehold, useHousehold } from "@/features/households/hooks/useHouseholds";
import { MemberCard } from "@/features/members/components/MemberCard";
import { useMembers } from "@/features/members/hooks/useMembers";

export function HouseholdDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [editOpen, setEditOpen] = useState(false);
  const { data: household, isLoading } = useHousehold(id);
  const { data: membersPage } = useMembers({ household: id });
  const deactivateHousehold = useDeactivateHousehold();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!household) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{household.household_name}</h1>
          <p className="text-sm text-muted-foreground">
            {household.household_code} · {household.member_count} members
          </p>
          {household.head_of_household_name && (
            <p className="text-sm text-muted-foreground">
              Head: {household.head_of_household_name}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <ChangeHeadDialog household={household} />
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                Edit
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit household</DialogTitle>
              </DialogHeader>
              <HouseholdForm household={household} onDone={() => setEditOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Members</h2>
        <div className="space-y-3">
          {(membersPage?.data ?? []).map((member) => (
            <MemberCard key={member.id} member={member} />
          ))}
          {membersPage?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No members assigned to this household yet.
            </p>
          )}
        </div>
      </div>

      {household.status === "active" && (
        <Button
          variant="destructive"
          size="sm"
          onClick={() => deactivateHousehold.mutate(household.id)}
          disabled={deactivateHousehold.isPending}
        >
          Deactivate household
        </Button>
      )}
    </div>
  );
}
