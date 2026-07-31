import { z } from "zod";

export const LOAN_SOURCES = ["internal", "external"] as const;
export const INTEREST_TYPES = ["none", "simple", "compound"] as const;
export const LOAN_PAYMENT_METHODS = ["cash", "bank", "upi", "card", "wallet", "cheque"] as const;

export const createLoanSchema = z
  .object({
    title: z.string().min(1, "Title is required.").max(200),
    description: z.string().optional().or(z.literal("")),
    borrower: z.string().min(1, "Select the borrower."),
    loan_source: z.enum(LOAN_SOURCES),
    lender: z.string().optional().or(z.literal("")),
    external_lender_name: z.string().optional().or(z.literal("")),
    household: z.string().optional().or(z.literal("")),
    loan_type: z.string().optional().or(z.literal("")),
    principal_amount: z
      .string()
      .min(1, "Principal amount is required.")
      .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
    interest_rate: z.string().optional().or(z.literal("")),
    interest_type: z.enum(INTEREST_TYPES),
    loan_date: z.string().min(1, "Loan date is required."),
    due_date: z.string().optional().or(z.literal("")),
    allow_overpayment: z.boolean().optional(),
  })
  .refine((data) => data.loan_source !== "internal" || data.lender, {
    message: "Select a lender for an internal loan.",
    path: ["lender"],
  })
  .refine((data) => data.loan_source !== "external" || data.external_lender_name, {
    message: "Enter the external lender's name.",
    path: ["external_lender_name"],
  });
export type CreateLoanFormValues = z.infer<typeof createLoanSchema>;

export const recordPaymentSchema = z.object({
  amount: z
    .string()
    .min(1, "Amount is required.")
    .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
  payment_date: z.string().min(1, "Date is required."),
  payment_method: z.enum(LOAN_PAYMENT_METHODS),
  remarks: z.string().optional().or(z.literal("")),
});
export type RecordPaymentFormValues = z.infer<typeof recordPaymentSchema>;

export const reminderSchema = z.object({
  member: z.string().min(1, "Select a member."),
  loan: z.string().optional().or(z.literal("")),
  reminder_type: z.enum(["due_date", "overdue", "installment", "custom"]),
  title: z.string().min(1, "Title is required.").max(200),
  message: z.string().optional().or(z.literal("")),
  remind_at: z.string().min(1, "Date/time is required."),
});
export type ReminderFormValues = z.infer<typeof reminderSchema>;
