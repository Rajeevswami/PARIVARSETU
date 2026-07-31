import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { User } from "@/types/user";

import { useUpdateProfile } from "../hooks/useAuth";
import { profileUpdateSchema, type ProfileUpdateFormValues } from "../schemas/authSchemas";

export function ProfileEditForm({ user }: { user: User }) {
  const updateProfile = useUpdateProfile();
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ProfileUpdateFormValues>({
    resolver: zodResolver(profileUpdateSchema),
    defaultValues: {
      first_name: user.first_name,
      last_name: user.last_name,
      gender: user.gender,
      date_of_birth: user.date_of_birth ?? "",
    },
  });

  const onSubmit = (values: ProfileUpdateFormValues) => updateProfile.mutate(values);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-md space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="first_name">First name</Label>
          <Input id="first_name" {...register("first_name")} />
          {errors.first_name && (
            <p className="text-sm text-destructive">{errors.first_name.message}</p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="last_name">Last name</Label>
          <Input id="last_name" {...register("last_name")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="date_of_birth">Date of birth</Label>
        <Input id="date_of_birth" type="date" {...register("date_of_birth")} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="gender">Gender</Label>
        <select
          id="gender"
          className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
          {...register("gender")}
        >
          <option value="">Prefer not to say</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
      </div>

      {updateProfile.isSuccess && <p className="text-sm text-muted-foreground">Profile updated.</p>}

      <Button type="submit" disabled={!isDirty || updateProfile.isPending}>
        {updateProfile.isPending ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
