import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Household } from "@/types/household";

import { useCreateHousehold, useUpdateHousehold } from "../hooks/useHouseholds";
import { householdSchema, type HouseholdFormValues } from "../schemas/householdSchemas";

export function HouseholdForm({
  household,
  onDone,
}: {
  household?: Household;
  onDone?: () => void;
}) {
  const createHousehold = useCreateHousehold();
  const updateHousehold = useUpdateHousehold();
  const isEdit = Boolean(household);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<HouseholdFormValues>({
    resolver: zodResolver(householdSchema),
    defaultValues: household
      ? {
          household_name: household.household_name,
          description: household.description,
          address: household.address,
          contact_number: household.contact_number,
        }
      : undefined,
  });

  const isPending = createHousehold.isPending || updateHousehold.isPending;

  const onSubmit = (values: HouseholdFormValues) => {
    if (isEdit && household) {
      updateHousehold.mutate({ id: household.id, data: values }, { onSuccess: onDone });
    } else {
      createHousehold.mutate(values, { onSuccess: onDone });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="household_name">Household name</Label>
        <Input id="household_name" {...register("household_name")} />
        {errors.household_name && (
          <p className="text-sm text-destructive">{errors.household_name.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="address">Address</Label>
        <Input id="address" {...register("address")} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="contact_number">Contact number</Label>
        <Input id="contact_number" {...register("contact_number")} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Input id="description" {...register("description")} />
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? "Saving…" : isEdit ? "Save changes" : "Create household"}
      </Button>
    </form>
  );
}
