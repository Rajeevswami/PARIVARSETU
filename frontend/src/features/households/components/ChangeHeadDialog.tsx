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
import { useMembers } from "@/features/members/hooks/useMembers";
import type { Household } from "@/types/household";

import { useChangeHead } from "../hooks/useHouseholds";

export function ChangeHeadDialog({ household }: { household: Household }) {
  const [open, setOpen] = useState(false);
  const [memberId, setMemberId] = useState("");
  const { data: membersPage } = useMembers({ household: household.id });
  const changeHead = useChangeHead();

  const members = membersPage?.data ?? [];

  const handleSubmit = () => {
    if (!memberId) return;
    changeHead.mutate({ householdId: household.id, memberId }, { onSuccess: () => setOpen(false) });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Change head
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change head of household</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="member">New head</Label>
            <select
              id="member"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              value={memberId}
              onChange={(e) => setMemberId(e.target.value)}
            >
              <option value="">Select a member</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>
          </div>

          {changeHead.isError && (
            <p className="text-sm text-destructive">Could not update the head of household.</p>
          )}

          <Button
            onClick={handleSubmit}
            className="w-full"
            disabled={!memberId || changeHead.isPending}
          >
            {changeHead.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
