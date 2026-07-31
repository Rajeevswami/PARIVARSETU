import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCategories } from "@/features/expenses/hooks/useExpenses";
import { useHouseholds } from "@/features/households/hooks/useHouseholds";
import type { Expense } from "@/types/expense";

import { useUpdateExpense } from "../hooks/useExpenses";
import {
  PAYMENT_METHODS,
  VISIBILITY_OPTIONS,
  editExpenseSchema,
  type EditExpenseFormValues,
} from "../schemas/expenseSchemas";

export function EditExpenseForm({ expense }: { expense: Expense }) {
  const updateExpense = useUpdateExpense();
  const { data: categories } = useCategories();
  const { data: householdsPage } = useHouseholds();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<EditExpenseFormValues>({
    resolver: zodResolver(editExpenseSchema),
    defaultValues: {
      title: expense.title,
      description: expense.description,
      expense_date: expense.expense_date,
      category: expense.category ?? "",
      household: expense.household ?? "",
      payment_method: expense.payment_method,
      visibility: expense.visibility,
      reference_number: expense.reference_number,
      notes: expense.notes,
    },
  });

  const onSubmit = (values: EditExpenseFormValues) =>
    updateExpense.mutate({
      id: expense.id,
      data: {
        ...values,
        category: values.category || null,
        household: values.household || null,
      },
    });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="title">Title</Label>
        <Input id="title" {...register("title")} />
        {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="expense_date">Date</Label>
          <Input id="expense_date" type="date" {...register("expense_date")} />
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
        <Label htmlFor="household">Household</Label>
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

      <div className="space-y-1.5">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" {...register("notes")} />
      </div>

      {updateExpense.isSuccess && <p className="text-sm text-muted-foreground">Saved.</p>}

      <Button type="submit" disabled={!isDirty || updateExpense.isPending}>
        {updateExpense.isPending ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
