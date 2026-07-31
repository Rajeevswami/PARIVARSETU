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

import { useRecordSettlement } from "../hooks/useBorrowLend";
import { settlementSchema, type SettlementFormValues } from "../schemas/borrowLendSchemas";

export function SettlementDialog({
  referenceType,
  referenceId,
  memberId,
  memberName,
}: {
  referenceType: "borrow" | "lend";
  referenceId: string;
  memberId: string;
  memberName: string;
}) {
  const [open, setOpen] = useState(false);
  const recordSettlement = useRecordSettlement();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SettlementFormValues>({
    resolver: zodResolver(settlementSchema),
    defaultValues: { member_id: memberId },
  });

  const onSubmit = (values: SettlementFormValues) =>
    recordSettlement.mutate(
      {
        reference_type: referenceType,
        reference_id: referenceId,
        member_id: values.member_id,
        amount: values.amount,
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

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Settle
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record settlement — {memberName}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <input type="hidden" {...register("member_id")} />

          <div className="space-y-1.5">
            <Label htmlFor="amount">Amount</Label>
            <Input id="amount" type="number" step="0.01" {...register("amount")} />
            {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
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

          {recordSettlement.isError && (
            <p className="text-sm text-destructive">
              {(recordSettlement.error as { response?: { data?: { message?: string } } })?.response
                ?.data?.message ?? "Could not record this settlement."}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={recordSettlement.isPending}>
            {recordSettlement.isPending ? "Saving…" : "Record settlement"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
