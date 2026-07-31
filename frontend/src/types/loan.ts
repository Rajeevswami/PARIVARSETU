export type InterestType = "none" | "simple" | "compound";
export type LoanSource = "internal" | "external";
export type LoanStatus = "draft" | "active" | "running" | "completed" | "cancelled" | "defaulted";
export type LoanPaymentMethod = "cash" | "bank" | "upi" | "card" | "wallet" | "cheque";

export interface LoanType {
  id: string;
  name: string;
  description: string;
  status: "active" | "inactive";
  created_at: string;
}

export interface LoanInstallment {
  id: string;
  installment_number: number;
  due_date: string;
  amount: string;
  paid_amount: string;
  status: "pending" | "partial" | "paid" | "overdue";
}

export interface LoanPayment {
  id: string;
  payment_number: string;
  payment_date: string;
  amount: string;
  interest_paid: string;
  principal_paid: string;
  remaining_balance: string;
  payment_method: LoanPaymentMethod;
  remarks: string;
  attachment: string | null;
  created_at: string;
}

export interface Loan {
  id: string;
  loan_number: string;
  household: string | null;
  household_name: string | null;
  borrower: string;
  borrower_name: string;
  loan_source: LoanSource;
  lender: string | null;
  lender_name: string | null;
  external_lender_name: string;
  loan_type: string | null;
  loan_type_name: string | null;
  title: string;
  description: string;
  principal_amount: string;
  interest_rate: string;
  interest_type: InterestType;
  interest_amount: string;
  total_amount: string;
  paid_amount: string;
  remaining_amount: string;
  loan_date: string;
  due_date: string | null;
  status: LoanStatus;
  allow_overpayment: boolean;
  installments: LoanInstallment[];
  payments: LoanPayment[];
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: string;
  loan: string | null;
  installment: string | null;
  member: string;
  member_name: string;
  reminder_type: "due_date" | "overdue" | "installment" | "custom";
  title: string;
  message: string;
  remind_at: string;
  status: "pending" | "sent" | "dismissed";
  created_at: string;
}

export interface LoanStats {
  grand_total: string;
  outstanding_total: string;
  by_status: { status: string; total: string; count: number }[];
  by_type: { loan_type__name: string | null; total: string }[];
}
