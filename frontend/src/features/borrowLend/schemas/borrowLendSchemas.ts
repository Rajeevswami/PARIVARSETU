import { z } from "zod";

export const TRANSACTION_PAYMENT_METHODS = [
  "cash",
  "bank",
  "upi",
  "card",
  "wallet",
  "cheque",
] as const;

export const createBorrowSchema = z
  .object({
    borrower: z.string().min(1, "Select the borrower."),
    lender: z.string().optional().or(z.literal("")),
    external_lender_name: z.string().optional().or(z.literal("")),
    household: z.string().optional().or(z.literal("")),
    amount: z
      .string()
      .min(1, "Amount is required.")
      .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
    date: z.string().min(1, "Date is required."),
    reason: z.string().optional().or(z.literal("")),
    payment_method: z.enum(TRANSACTION_PAYMENT_METHODS),
  })
  .refine((data) => data.lender || data.external_lender_name, {
    message: "Provide either an internal lender or an external lender name.",
    path: ["external_lender_name"],
  });
export type CreateBorrowFormValues = z.infer<typeof createBorrowSchema>;

export const createLendSchema = z
  .object({
    giver: z.string().min(1, "Select the giver."),
    receiver: z.string().optional().or(z.literal("")),
    external_receiver_name: z.string().optional().or(z.literal("")),
    household: z.string().optional().or(z.literal("")),
    amount: z
      .string()
      .min(1, "Amount is required.")
      .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
    date: z.string().min(1, "Date is required."),
    reason: z.string().optional().or(z.literal("")),
    payment_method: z.enum(TRANSACTION_PAYMENT_METHODS),
  })
  .refine((data) => data.receiver || data.external_receiver_name, {
    message: "Provide either an internal receiver or an external receiver name.",
    path: ["external_receiver_name"],
  });
export type CreateLendFormValues = z.infer<typeof createLendSchema>;

export const settlementSchema = z.object({
  member_id: z.string().min(1, "Select a member."),
  amount: z
    .string()
    .min(1, "Amount is required.")
    .refine((v) => !Number.isNaN(Number(v)) && Number(v) > 0, "Must be greater than zero."),
  settlement_date: z.string().min(1, "Date is required."),
  remarks: z.string().optional().or(z.literal("")),
});
export type SettlementFormValues = z.infer<typeof settlementSchema>;
