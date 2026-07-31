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
import type { Expense } from "@/types/expense";

import { useSettleExpense } from "../hooks/useExpenses";
import { settlementSchema, type SettlementFormValues } from "../schemas/expenseSchemas";

export function SettlementDialog({ expense }: { expense: Expense }) {
  const [open, setOpen] = useState(false);
  const settleExpense = useSettleExpense(expense.id);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SettlementFormValues>({ resolver: zodResolver(settlementSchema) });

  const pendingParticipants = expense.participants.filter((p) => p.status !== "settled");

  const onSubmit = (values: SettlementFormValues) =>
    settleExpense.mutate(
      {
        member_id: values.member_id,
        paid_amount: values.paid_amount,
        settlement_date: values.settlement_date,
        remarks: values.remarks || undefined,
      },
      {
        onSuccess: () => {
          reset();
          setOpen(false);
        },
      }
    );

  if (pendingParticipants.length === 0) return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Record settlement
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record settlement</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="member_id">Member</Label>
            <select
              id="member_id"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("member_id")}
            >
              <option value="">Select</option>
              {pendingParticipants.map((p) => (
                <option key={p.member} value={p.member}>
                  {p.member_name} — pending {p.pending_amount}
                </option>
              ))}
            </select>
            {errors.member_id && (
              <p className="text-sm text-destructive">{errors.member_id.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="paid_amount">Amount</Label>
            <Input id="paid_amount" type="number" step="0.01" {...register("paid_amount")} />
            {errors.paid_amount && (
              <p className="text-sm text-destructive">{errors.paid_amount.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="settlement_date">Date</Label>
            <Input id="settlement_date" type="date" {...register("settlement_date")} />
            {errors.settlement_date && (
              <p className="text-sm text-destructive">{errors.settlement_date.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="remarks">Remarks</Label>
            <Input id="remarks" {...register("remarks")} />
          </div>

          {settleExpense.isError && (
            <p className="text-sm text-destructive">
              {(settleExpense.error as { response?: { data?: { message?: string } } })?.response
                ?.data?.message ?? "Could not record this settlement."}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={settleExpense.isPending}>
            {settleExpense.isPending ? "Saving…" : "Record settlement"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
