import { Link } from "react-router-dom";

import type { Loan } from "@/types/loan";

const STATUS_COLOR: Record<string, string> = {
  draft: "text-muted-foreground",
  active: "text-blue-600 dark:text-blue-400",
  running: "text-amber-600 dark:text-amber-400",
  completed: "text-green-600 dark:text-green-400",
  cancelled: "text-destructive",
  defaulted: "text-destructive",
};

export function LoanCard({ loan }: { loan: Loan }) {
  return (
    <Link
      to={`/loans/${loan.id}`}
      className="block rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{loan.title}</h3>
        <span className="font-semibold">{loan.total_amount}</span>
      </div>
      <div className="mt-1 flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {loan.borrower_name} ← {loan.lender_name || loan.external_lender_name}
        </span>
        <span className={STATUS_COLOR[loan.status]}>{loan.status}</span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {loan.loan_number} · Remaining {loan.remaining_amount}
      </p>
    </Link>
  );
}
