import { z } from "zod";

export const journalLineSchema = z.object({
  ledger_account: z.string().min(1, "Select an account."),
  entry_type: z.enum(["debit", "credit"]),
  amount: z
    .string()
    .min(1, "Amount is required.")
    .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
  description: z.string().optional().or(z.literal("")),
});
export type JournalLineFormValues = z.infer<typeof journalLineSchema>;

export const createJournalSchema = z.object({
  journal_date: z.string().min(1, "Date is required."),
  description: z.string().optional().or(z.literal("")),
  lines: z.array(journalLineSchema).min(2, "A journal needs at least two lines."),
});
export type CreateJournalFormValues = z.infer<typeof createJournalSchema>;

export const createAccountSchema = z.object({
  account_code: z.string().min(1, "Code is required.").max(20),
  account_name: z.string().min(1, "Name is required.").max(150),
  account_group: z.string().min(1, "Select a group."),
  description: z.string().optional().or(z.literal("")),
});
export type CreateAccountFormValues = z.infer<typeof createAccountSchema>;
