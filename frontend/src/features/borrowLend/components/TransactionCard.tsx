import type { BorrowTransaction, LendTransaction } from "@/types/borrowLend";

export function BorrowCard({ transaction }: { transaction: BorrowTransaction }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{transaction.borrower_name}</h3>
        <span className="font-semibold">{transaction.amount}</span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        From {transaction.lender_name || transaction.external_lender_name} · {transaction.date}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        {transaction.transaction_number} · {transaction.status} · Remaining{" "}
        {transaction.remaining_amount}
      </p>
    </div>
  );
}

export function LendCard({ transaction }: { transaction: LendTransaction }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{transaction.giver_name}</h3>
        <span className="font-semibold">{transaction.amount}</span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        To {transaction.receiver_name || transaction.external_receiver_name} · {transaction.date}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        {transaction.transaction_number} · {transaction.status} · Remaining{" "}
        {transaction.remaining_amount}
      </p>
    </div>
  );
}
