import { zodResolver } from "@hookform/resolvers/zod";
import { useMemo, useState } from "react";
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
import { useHouseholds } from "@/features/households/hooks/useHouseholds";
import { useMembers } from "@/features/members/hooks/useMembers";

import { useCategories, useCreateExpense } from "../hooks/useExpenses";
import {
  PAYMENT_METHODS,
  SPLIT_TYPES,
  VISIBILITY_OPTIONS,
  createExpenseSchema,
  type CreateExpenseFormValues,
} from "../schemas/expenseSchemas";

export function CreateExpenseDialog() {
  const [open, setOpen] = useState(false);
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);
  const [participantValues, setParticipantValues] = useState<Record<string, string>>({});

  const createExpense = useCreateExpense();
  const { data: membersPage } = useMembers();
  const { data: householdsPage } = useHouseholds();
  const { data: categories } = useCategories();
  const members = membersPage?.data ?? [];
  const [participantsError, setParticipantsError] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<CreateExpenseFormValues>({
    resolver: zodResolver(createExpenseSchema),
    defaultValues: { split_type: "equal", visibility: "household", payment_method: "cash" },
  });

  const splitType = watch("split_type");
  const amount = watch("amount");

  const toggleMember = (memberId: string) => {
    setSelectedMemberIds((prev) =>
      prev.includes(memberId) ? prev.filter((id) => id !== memberId) : [...prev, memberId]
    );
  };

  const previewShares = useMemo(() => {
    if (splitType !== "equal" || !amount || selectedMemberIds.length === 0) return null;
    const total = Number(amount);
    if (Number.isNaN(total)) return null;
    const base = Math.floor((total / selectedMemberIds.length) * 100) / 100;
    return base;
  }, [splitType, amount, selectedMemberIds]);

  const onSubmit = (values: CreateExpenseFormValues) => {
    if (selectedMemberIds.length === 0) {
      setParticipantsError("Select at least one participant.");
      return;
    }
    if (values.split_type !== "equal") {
      const missing = selectedMemberIds.some((id) => !participantValues[id]);
      if (missing) {
        setParticipantsError(
          values.split_type === "percentage"
            ? "Enter a percentage for every selected participant."
            : "Enter an amount for every selected participant."
        );
        return;
      }
    }
    setParticipantsError("");

    const participants = selectedMemberIds.map((member_id) => ({
      member_id,
      value: values.split_type === "equal" ? undefined : participantValues[member_id],
    }));

    createExpense.mutate(
      {
        title: values.title,
        description: values.description || undefined,
        expense_date: values.expense_date,
        amount: values.amount,
        paid_by: values.paid_by,
        household: values.household || undefined,
        category: values.category || undefined,
        payment_method: values.payment_method,
        visibility: values.visibility,
        reference_number: values.reference_number || undefined,
        notes: values.notes || undefined,
        split_type: values.split_type,
        participants,
      },
      {
        onSuccess: () => {
          reset();
          setSelectedMemberIds([]);
          setParticipantValues({});
          setOpen(false);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add expense</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add expense</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input id="title" {...register("title")} />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount</Label>
              <Input id="amount" type="number" step="0.01" {...register("amount")} />
              {errors.amount && <p className="text-sm text-destructive">{errors.amount.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="expense_date">Date</Label>
              <Input id="expense_date" type="date" {...register("expense_date")} />
              {errors.expense_date && (
                <p className="text-sm text-destructive">{errors.expense_date.message}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="paid_by">Paid by</Label>
              <select
                id="paid_by"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("paid_by")}
              >
                <option value="">Select</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.display_name}
                  </option>
                ))}
              </select>
              {errors.paid_by && (
                <p className="text-sm text-destructive">{errors.paid_by.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="payment_method">Payment method</Label>
              <select
                id="payment_method"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("payment_method")}
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("category")}
              >
                <option value="">None</option>
                {(categories ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="visibility">Visibility</Label>
              <select
                id="visibility"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("visibility")}
              >
                {VISIBILITY_OPTIONS.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="household">Household (optional)</Label>
            <select
              id="household"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("household")}
            >
              <option value="">None</option>
              {(householdsPage?.data ?? []).map((h) => (
                <option key={h.id} value={h.id}>
                  {h.household_name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5 rounded-md border border-border p-3">
            <Label>Split</Label>
            <select
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("split_type")}
            >
              {SPLIT_TYPES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            <div className="max-h-48 space-y-2 overflow-y-auto pt-2">
              {members.map((m) => {
                const selected = selectedMemberIds.includes(m.id);
                return (
                  <div key={m.id} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => toggleMember(m.id)}
                      id={`member-${m.id}`}
                    />
                    <label htmlFor={`member-${m.id}`} className="flex-1 text-sm">
                      {m.display_name}
                    </label>
                    {selected && splitType !== "equal" && (
                      <Input
                        type="number"
                        step="0.01"
                        placeholder={splitType === "percentage" ? "%" : "amount"}
                        className="w-24"
                        value={participantValues[m.id] ?? ""}
                        onChange={(e) =>
                          setParticipantValues((prev) => ({ ...prev, [m.id]: e.target.value }))
                        }
                      />
                    )}
                    {selected && splitType === "equal" && previewShares !== null && (
                      <span className="w-24 text-right text-xs text-muted-foreground">
                        ≈ {previewShares.toFixed(2)}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
            {participantsError && <p className="text-sm text-destructive">{participantsError}</p>}
          </div>

          {createExpense.isError && (
            <p className="text-sm text-destructive">
              {(createExpense.error as { response?: { data?: { message?: string } } })?.response
                ?.data?.message ?? "Could not create the expense."}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={createExpense.isPending}>
            {createExpense.isPending ? "Saving…" : "Create expense"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
