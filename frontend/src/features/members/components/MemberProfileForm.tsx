import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Member } from "@/types/member";

import { useUpdateMember } from "../hooks/useMembers";
import {
  RELATIONSHIP_OPTIONS,
  memberProfileSchema,
  type MemberProfileFormValues,
} from "../schemas/memberSchemas";

export function MemberProfileForm({ member }: { member: Member }) {
  const updateMember = useUpdateMember();
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<MemberProfileFormValues>({
    resolver: zodResolver(memberProfileSchema),
    defaultValues: {
      display_name: member.display_name,
      relationship: member.relationship,
      gender: member.gender,
      blood_group: member.blood_group,
      marital_status: member.marital_status,
      occupation: member.occupation,
      date_of_birth: member.date_of_birth ?? "",
      emergency_contact: member.emergency_contact,
      notes: member.notes,
    },
  });

  const onSubmit = (values: MemberProfileFormValues) =>
    updateMember.mutate({ id: member.id, data: values });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-lg space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="display_name">Display name</Label>
        <Input id="display_name" {...register("display_name")} />
        {errors.display_name && (
          <p className="text-sm text-destructive">{errors.display_name.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
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
          <Label htmlFor="occupation">Occupation</Label>
          <Input id="occupation" {...register("occupation")} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="date_of_birth">Date of birth</Label>
          <Input id="date_of_birth" type="date" {...register("date_of_birth")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="emergency_contact">Emergency contact</Label>
          <Input id="emergency_contact" {...register("emergency_contact")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" {...register("notes")} />
      </div>

      {updateMember.isSuccess && <p className="text-sm text-muted-foreground">Saved.</p>}

      <Button type="submit" disabled={!isDirty || updateMember.isPending}>
        {updateMember.isPending ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
