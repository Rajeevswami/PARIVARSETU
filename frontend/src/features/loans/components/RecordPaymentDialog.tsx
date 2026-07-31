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
import type { Loan } from "@/types/loan";

import { useRecordPayment } from "../hooks/useLoans";
import {
  LOAN_PAYMENT_METHODS,
  recordPaymentSchema,
  type RecordPaymentFormValues,
} from "../schemas/loanSchemas";

export function RecordPaymentDialog({ loan }: { loan: Loan }) {
  const [open, setOpen] = useState(false);
  const recordPayment = useRecordPayment(loan.id);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RecordPaymentFormValues>({ resolver: zodResolver(recordPaymentSchema) });

  const onSubmit = (values: RecordPaymentFormValues) =>
    recordPayment.mutate(
      {
        amount: values.amount,
        payment_date: values.payment_date,
        payment_method: values.payment_method,
        remarks: values.remarks || undefined,
      },
      {
        onSuccess: () => {
          reset();
          setOpen(false);
        },
      }
    );

  if (loan.status === "completed" || loan.status === "cancelled") return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Record payment</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record payment — remaining {loan.remaining_amount}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="amount">Amount</Label>
            <Input id="amount" type="number" step="0.01" {...register("amount")} />
            {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="payment_date">Date</Label>
            <Input id="payment_date" type="date" {...register("payment_date")} />
            {errors.payment_date && (
              <p className="text-sm text-destructive">{errors.payment_date.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="payment_method">Payment method</Label>
            <select
              id="payment_method"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("payment_method")}
            >
              {LOAN_PAYMENT_METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="remarks">Remarks</Label>
            <Input id="remarks" {...register("remarks")} />
          </div>

          {recordPayment.isError && (
            <p className="text-sm text-destructive">
              {(recordPayment.error as { response?: { data?: { message?: string } } })?.response
                ?.data?.message ?? "Could not record this payment."}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={recordPayment.isPending}>
            {recordPayment.isPending ? "Saving…" : "Record payment"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
