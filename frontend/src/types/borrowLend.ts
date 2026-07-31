export type TransactionPaymentMethod = "cash" | "bank" | "upi" | "card" | "wallet" | "cheque";
export type TransactionStatus = "pending" | "partially_settled" | "settled" | "cancelled";

export interface BorrowTransaction {
  id: string;
  transaction_number: string;
  household: string | null;
  household_name: string | null;
  borrower: string;
  borrower_name: string;
  lender: string | null;
  lender_name: string | null;
  external_lender_name: string;
  amount: string;
  date: string;
  reason: string;
  payment_method: TransactionPaymentMethod;
  status: TransactionStatus;
  settled_amount: string;
  remaining_amount: string;
  created_at: string;
}

export interface LendTransaction {
  id: string;
  transaction_number: string;
  household: string | null;
  household_name: string | null;
  giver: string;
  giver_name: string;
  receiver: string | null;
  receiver_name: string | null;
  external_receiver_name: string;
  amount: string;
  date: string;
  reason: string;
  payment_method: TransactionPaymentMethod;
  status: TransactionStatus;
  settled_amount: string;
  remaining_amount: string;
  created_at: string;
}

export interface Settlement {
  id: string;
  reference_type: "borrow" | "lend";
  reference_id: string;
  member: string;
  amount: string;
  settled_amount: string;
  remaining_amount: string;
  status: "recorded" | "reversed";
  settlement_date: string;
  remarks: string;
  created_at: string;
}
