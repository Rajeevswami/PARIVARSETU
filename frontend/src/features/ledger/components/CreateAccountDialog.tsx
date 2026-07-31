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

import { useAccountGroups, useCreateLedgerAccount } from "../hooks/useLedger";
import { createAccountSchema, type CreateAccountFormValues } from "../schemas/ledgerSchemas";

export function CreateAccountDialog() {
  const [open, setOpen] = useState(false);
  const { data: groups } = useAccountGroups();
  const createAccount = useCreateLedgerAccount();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateAccountFormValues>({ resolver: zodResolver(createAccountSchema) });

  const onSubmit = (values: CreateAccountFormValues) =>
    createAccount.mutate(values, {
      onSuccess: () => {
        reset();
        setOpen(false);
      },
    });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">New account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New ledger account</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="account_code">Code</Label>
              <Input id="account_code" {...register("account_code")} />
              {errors.account_code && (
                <p className="text-sm text-destructive">{errors.account_code.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="account_group">Group</Label>
              <select
                id="account_group"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("account_group")}
              >
                <option value="">Select</option>
                {(groups ?? []).map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
              {errors.account_group && (
                <p className="text-sm text-destructive">{errors.account_group.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="account_name">Name</Label>
            <Input id="account_name" {...register("account_name")} />
            {errors.account_name && (
              <p className="text-sm text-destructive">{errors.account_name.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <Input id="description" {...register("description")} />
          </div>

          {createAccount.isError && (
            <p className="text-sm text-destructive">Could not create this account.</p>
          )}

          <Button type="submit" className="w-full" disabled={createAccount.isPending}>
            {createAccount.isPending ? "Saving…" : "Create account"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
