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
import { useHouseholds } from "@/features/households/hooks/useHouseholds";
import { useMembers } from "@/features/members/hooks/useMembers";

import { useCreateLoan, useLoanTypes } from "../hooks/useLoans";
import {
  INTEREST_TYPES,
  LOAN_SOURCES,
  createLoanSchema,
  type CreateLoanFormValues,
} from "../schemas/loanSchemas";

export function CreateLoanDialog() {
  const [open, setOpen] = useState(false);
  const createLoan = useCreateLoan();
  const { data: membersPage } = useMembers();
  const { data: householdsPage } = useHouseholds();
  const { data: loanTypes } = useLoanTypes();
  const members = membersPage?.data ?? [];

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<CreateLoanFormValues>({
    resolver: zodResolver(createLoanSchema),
    defaultValues: { loan_source: "external", interest_type: "none" },
  });

  const loanSource = watch("loan_source");
  const interestType = watch("interest_type");

  const onSubmit = (values: CreateLoanFormValues) =>
    createLoan.mutate(
      {
        title: values.title,
        description: values.description || undefined,
        borrower: values.borrower,
        loan_source: values.loan_source,
        lender: values.lender || undefined,
        external_lender_name: values.external_lender_name || undefined,
        household: values.household || undefined,
        loan_type: values.loan_type || undefined,
        principal_amount: values.principal_amount,
        interest_rate: values.interest_rate || undefined,
        interest_type: values.interest_type,
        loan_date: values.loan_date,
        due_date: values.due_date || undefined,
        allow_overpayment: values.allow_overpayment,
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
        <Button>New loan</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New loan</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input id="title" {...register("title")} />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="borrower">Borrower</Label>
            <select
              id="borrower"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("borrower")}
            >
              <option value="">Select</option>
              {members.map((m) => (
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
            <Label htmlFor="loan_source">Loan source</Label>
            <select
              id="loan_source"
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
              {...register("loan_source")}
            >
              {LOAN_SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {loanSource === "internal" ? (
            <div className="space-y-1.5">
              <Label htmlFor="lender">Lender</Label>
              <select
                id="lender"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("lender")}
              >
                <option value="">Select</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.display_name}
                  </option>
                ))}
              </select>
              {errors.lender && <p className="text-sm text-destructive">{errors.lender.message}</p>}
            </div>
          ) : (
            <div className="space-y-1.5">
              <Label htmlFor="external_lender_name">External lender name</Label>
              <Input id="external_lender_name" {...register("external_lender_name")} />
              {errors.external_lender_name && (
                <p className="text-sm text-destructive">{errors.external_lender_name.message}</p>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="principal_amount">Principal</Label>
              <Input
                id="principal_amount"
                type="number"
                step="0.01"
                {...register("principal_amount")}
              />
              {errors.principal_amount && (
                <p className="text-sm text-destructive">{errors.principal_amount.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="loan_date">Loan date</Label>
              <Input id="loan_date" type="date" {...register("loan_date")} />
              {errors.loan_date && (
                <p className="text-sm text-destructive">{errors.loan_date.message}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="interest_type">Interest type</Label>
              <select
                id="interest_type"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("interest_type")}
              >
                {INTEREST_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            {interestType !== "none" && (
              <div className="space-y-1.5">
                <Label htmlFor="interest_rate">Annual rate (%)</Label>
                <Input
                  id="interest_rate"
                  type="number"
                  step="0.01"
                  {...register("interest_rate")}
                />
              </div>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="due_date">Due date (optional)</Label>
            <Input id="due_date" type="date" {...register("due_date")} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="loan_type">Loan type</Label>
              <select
                id="loan_type"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                {...register("loan_type")}
              >
                <option value="">None</option>
                {(loanTypes ?? []).map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
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
          </div>

          <div className="flex items-center gap-2">
            <input type="checkbox" id="allow_overpayment" {...register("allow_overpayment")} />
            <Label htmlFor="allow_overpayment" className="font-normal">
              Allow payments larger than the remaining balance
            </Label>
          </div>

          {createLoan.isError && (
            <p className="text-sm text-destructive">
              {(createLoan.error as { response?: { data?: { message?: string } } })?.response?.data
                ?.message ?? "Could not create the loan."}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={createLoan.isPending}>
            {createLoan.isPending ? "Saving…" : "Create loan"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
