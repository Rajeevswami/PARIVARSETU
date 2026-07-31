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
import { useMembers } from "@/features/members/hooks/useMembers";

import { useCreateBorrow } from "../hooks/useBorrowLend";
import {
  TRANSACTION_PAYMENT_METHODS,
  createBorrowSchema,
  type CreateBorrowFormValues,
} from "../schemas/borrowLendSchemas";

export function CreateBorrowDialog() {
  const [open, setOpen] = useState(false);
  const createBorrow = useCreateBorrow();
  const { data: membersPage } = useMembers();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateBorrowFormValues>({ resolver: zodResolver(createBorrowSchema) });

  const onSubmit = (values: CreateBorrowFormValues) =>
    createBorrow.mutate(
      {
        borrower: values.borrower,
        lender: values.lender || undefined,
        external_lender_name: values.external_lender_name || undefined,
        amount: values.amount,
        date: values.date,
        reason: values.reason || undefined,
        payment_method: values.payment_method,
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
        <Button>New borrow</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record a borrow</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="borrower">Borrower</Label>
            <select
              id="borrower"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("borrower")}
            >
              <option value="">Select</option>
              {(membersPage?.data ?? []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>
            {errors.borrower && (
              <p className="text-sm text-destructive">{errors.borrower.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="external_lender_name">
              External lender (or leave blank and pick a member below)
            </Label>
            <Input id="external_lender_name" {...register("external_lender_name")} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="lender">Lender (family member)</Label>
            <select
              id="lender"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("lender")}
            >
              <option value="">None</option>
              {(membersPage?.data ?? []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>
            {errors.external_lender_name && (
              <p className="text-sm text-destructive">{errors.external_lender_name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} />
              {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="date">Date</Label>
              <Input id="date" type="date" {...register("date")} />
              {errors.date && <p className="text-sm text-destructive">{errors.date.message}</p>}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="payment_method">Payment method</Label>
            <select
              id="payment_method"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("payment_method")}
            >
              {TRANSACTION_PAYMENT_METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reason">Reason</Label>
            <Input id="reason" {...register("reason")} />
          </div>

          {createBorrow.isError && (
            <p className="text-sm text-destructive">Could not record this borrow transaction.</p>
          )}

          <Button type="submit" className="w-full" disabled={createBorrow.isPending}>
            {createBorrow.isPending ? "Saving…" : "Record borrow"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
