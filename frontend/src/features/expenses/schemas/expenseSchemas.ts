import { z } from "zod";

export const PAYMENT_METHODS = ["cash", "bank", "upi", "card", "wallet", "cheque"] as const;
export const VISIBILITY_OPTIONS = ["private", "household", "family"] as const;
export const SPLIT_TYPES = ["equal", "percentage", "fixed", "custom"] as const;

export const participantInputSchema = z.object({
  member_id: z.string().min(1),
  value: z.string().optional(),
});

export const createExpenseSchema = z.object({
  title: z.string().min(1, "Title is required.").max(200),
  description: z.string().optional().or(z.literal("")),
  expense_date: z.string().min(1, "Date is required."),
  amount: z
    .string()
    .min(1, "Amount is required.")
    .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Amount must be greater than zero."),
  paid_by: z.string().min(1, "Select who paid."),
  household: z.string().optional().or(z.literal("")),
  category: z.string().optional().or(z.literal("")),
  payment_method: z.enum(PAYMENT_METHODS),
  visibility: z.enum(VISIBILITY_OPTIONS),
  reference_number: z.string().optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
  split_type: z.enum(SPLIT_TYPES),
});
export type CreateExpenseFormValues = z.infer<typeof createExpenseSchema>;

export const editExpenseSchema = z.object({
  title: z.string().min(1, "Title is required.").max(200),
  description: z.string().optional().or(z.literal("")),
  expense_date: z.string().min(1),
  category: z.string().optional().or(z.literal("")),
  household: z.string().optional().or(z.literal("")),
  payment_method: z.enum(PAYMENT_METHODS),
  visibility: z.enum(VISIBILITY_OPTIONS),
  reference_number: z.string().optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});
export type EditExpenseFormValues = z.infer<typeof editExpenseSchema>;

export const settlementSchema = z.object({
  member_id: z.string().min(1, "Select a member."),
  paid_amount: z
    .string()
    .min(1, "Amount is required.")
    .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Amount must be greater than zero."),
  settlement_date: z.string().min(1, "Date is required."),
  remarks: z.string().optional().or(z.literal("")),
});
export type SettlementFormValues = z.infer<typeof settlementSchema>;

export const categorySchema = z.object({
  name: z.string().min(1, "Name is required.").max(100),
  description: z.string().optional().or(z.literal("")),
  color: z.string().optional().or(z.literal("")),
});
export type CategoryFormValues = z.infer<typeof categorySchema>;
