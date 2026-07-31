export type ExpensePaymentMethod = "cash" | "bank" | "upi" | "card" | "wallet" | "cheque";
export type ExpenseVisibility = "private" | "household" | "family";
export type ExpenseStatus = "draft" | "pending" | "approved" | "settled" | "cancelled";
export type SplitType = "equal" | "percentage" | "fixed" | "custom";

export interface ExpenseCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  sort_order: number;
  status: "active" | "inactive";
  created_at: string;
}

export interface ExpenseParticipant {
  id: string;
  member: string;
  member_name: string;
  share_amount: string;
  share_percentage: string | null;
  settled_amount: string;
  pending_amount: string;
  status: "pending" | "partially_settled" | "settled";
}

export interface ExpenseAttachment {
  id: string;
  file: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  checksum: string;
  uploaded_by: string;
  created_at: string;
}

export interface ExpenseComment {
  id: string;
  member: string;
  member_name: string;
  comment: string;
  created_at: string;
}

export interface ExpenseSettlement {
  id: string;
  member: string;
  paid_amount: string;
  received_amount: string;
  remaining_amount: string;
  settlement_date: string;
  remarks: string;
  status: "recorded" | "reversed";
  created_at: string;
}

export interface Expense {
  id: string;
  expense_number: string;
  household: string | null;
  household_name: string | null;
  category: string | null;
  category_name: string | null;
  title: string;
  description: string;
  expense_date: string;
  amount: string;
  currency: string;
  paid_by: string;
  paid_by_name: string;
  payment_method: ExpensePaymentMethod;
  visibility: ExpenseVisibility;
  status: ExpenseStatus;
  reference_number: string;
  notes: string;
  participants: ExpenseParticipant[];
  attachments: ExpenseAttachment[];
  settlements: ExpenseSettlement[];
  total_settled: string;
  created_at: string;
  updated_at: string;
}

export interface ExpenseStats {
  grand_total: string;
  by_category: { category__name: string | null; total: string }[];
  by_household: { household__household_name: string | null; total: string }[];
  by_member: { paid_by__display_name: string; total: string }[];
  by_status: { status: string; total: string; count: number }[];
}
