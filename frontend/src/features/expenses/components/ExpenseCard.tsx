import { Link } from "react-router-dom";

import type { Expense } from "@/types/expense";

const STATUS_COLOR: Record<string, string> = {
  draft: "text-muted-foreground",
  pending: "text-amber-600 dark:text-amber-400",
  approved: "text-blue-600 dark:text-blue-400",
  settled: "text-green-600 dark:text-green-400",
  cancelled: "text-destructive",
};

export function ExpenseCard({ expense }: { expense: Expense }) {
  return (
    <Link
      to={`/expenses/${expense.id}`}
      className="block rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{expense.title}</h3>
        <span className="font-semibold">
          {expense.currency} {expense.amount}
        </span>
      </div>
      <div className="mt-1 flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {expense.category_name || "Uncategorized"} · {expense.paid_by_name}
        </span>
        <span className={STATUS_COLOR[expense.status]}>{expense.status}</span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {expense.expense_number} · {expense.expense_date}
      </p>
    </Link>
  );
}
