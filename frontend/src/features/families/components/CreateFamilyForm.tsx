import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useCreateFamily } from "../hooks/useFamilies";
import { createFamilySchema, type CreateFamilyFormValues } from "../schemas/familySchemas";

export function CreateFamilyForm() {
  const createFamily = useCreateFamily();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateFamilyFormValues>({ resolver: zodResolver(createFamilySchema) });

  const onSubmit = (values: CreateFamilyFormValues) => createFamily.mutate(values);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-md space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="family_name">Family name</Label>
        <Input id="family_name" placeholder="e.g. Sharma Family" {...register("family_name")} />
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
        <Input id="description" placeholder="Optional" {...register("description")} />
      </div>

      {createFamily.isError && (
        <p className="text-sm text-destructive">Could not create your family. Please try again.</p>
      )}

      <Button type="submit" className="w-full" disabled={createFamily.isPending}>
        {createFamily.isPending ? "Creating…" : "Create family"}
      </Button>
    </form>
  );
}
