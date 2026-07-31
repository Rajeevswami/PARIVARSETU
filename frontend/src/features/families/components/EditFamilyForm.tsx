import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Family } from "@/types/family";

import { useUpdateFamily } from "../hooks/useFamilies";
import { editFamilySchema, type EditFamilyFormValues } from "../schemas/familySchemas";

export function EditFamilyForm({ family }: { family: Family }) {
  const updateFamily = useUpdateFamily();
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<EditFamilyFormValues>({
    resolver: zodResolver(editFamilySchema),
    defaultValues: {
      family_name: family.family_name,
      description: family.description,
      country: family.country,
      state: family.state,
      city: family.city,
    },
  });

  const onSubmit = (values: EditFamilyFormValues) =>
    updateFamily.mutate({ id: family.id, data: values });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-md space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="family_name">Family name</Label>
        <Input id="family_name" {...register("family_name")} />
        {errors.family_name && (
          <p className="text-sm text-destructive">{errors.family_name.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="city">City</Label>
          <Input id="city" {...register("city")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="state">State</Label>
          <Input id="state" {...register("state")} />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Input id="description" {...register("description")} />
      </div>

      {updateFamily.isSuccess && <p className="text-sm text-muted-foreground">Saved.</p>}

      <Button type="submit" disabled={!isDirty || updateFamily.isPending}>
        {updateFamily.isPending ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
