import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useHouseholds } from "@/features/households/hooks/useHouseholds";
import type { Member } from "@/types/member";

import { useTransferMember } from "../hooks/useMembers";

export function TransferMemberDialog({ member }: { member: Member }) {
  const [open, setOpen] = useState(false);
  const [householdId, setHouseholdId] = useState(member.household ?? "");
  const { data: householdsPage } = useHouseholds();
  const transferMember = useTransferMember();

  const handleSubmit = () => {
    transferMember.mutate(
      { id: member.id, householdId: householdId || null },
      { onSuccess: () => setOpen(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Transfer
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Transfer {member.display_name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="household">New household</Label>
            <select
              id="household"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              value={householdId}
              onChange={(e) => setHouseholdId(e.target.value)}
            >
              <option value="">Unassigned</option>
              {(householdsPage?.data ?? []).map((h) => (
                <option key={h.id} value={h.id}>
                  {h.household_name}
                </option>
              ))}
            </select>
          </div>

          {transferMember.isError && (
            <p className="text-sm text-destructive">Could not transfer this member.</p>
          )}

          <Button onClick={handleSubmit} className="w-full" disabled={transferMember.isPending}>
            {transferMember.isPending ? "Transferring…" : "Confirm transfer"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
