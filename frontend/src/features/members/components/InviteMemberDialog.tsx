import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useHouseholds } from "@/features/households/hooks/useHouseholds";

import { useInviteMember } from "../hooks/useMembers";
import {
  RELATIONSHIP_OPTIONS,
  inviteMemberSchema,
  type InviteMemberFormValues,
} from "../schemas/memberSchemas";

export function InviteMemberDialog() {
  const [open, setOpen] = useState(false);
  const inviteMember = useInviteMember();
  const { data: householdsPage } = useHouseholds();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InviteMemberFormValues>({ resolver: zodResolver(inviteMemberSchema) });

  const onSubmit = (values: InviteMemberFormValues) =>
    inviteMember.mutate(
      {
        email: values.email || undefined,
        mobile: values.mobile || undefined,
        household: values.household || undefined,
        relationship: values.relationship || undefined,
      },
      {
        onSuccess: () => {
          reset();
          setOpen(false);
        },
      }
    );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Invite member</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite a family member</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register("email")} />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mobile">Mobile (optional if email given)</Label>
            <Input id="mobile" {...register("mobile")} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="relationship">Relationship</Label>
            <select
              id="relationship"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("relationship")}
            >
              <option value="">Select</option>
              {RELATIONSHIP_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="household">Household (optional)</Label>
            <select
              id="household"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("household")}
            >
              <option value="">Not assigned yet</option>
              {(householdsPage?.data ?? []).map((h) => (
                <option key={h.id} value={h.id}>
                  {h.household_name}
                </option>
              ))}
            </select>
          </div>

          {inviteMember.isError && (
            <p className="text-sm text-destructive">Could not send the invitation.</p>
          )}

          <Button type="submit" className="w-full" disabled={inviteMember.isPending}>
            {inviteMember.isPending ? "Sending…" : "Send invitation"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
