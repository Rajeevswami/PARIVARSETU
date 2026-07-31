import { useNavigate } from "react-router-dom";

import type { Expense } from "@/types/expense";

export function ExpenseTable({ expenses }: { expenses: Expense[] }) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Number</th>
            <th className="px-3 py-2 font-medium">Title</th>
            <th className="px-3 py-2 font-medium">Category</th>
            <th className="px-3 py-2 font-medium">Paid by</th>
            <th className="px-3 py-2 text-right font-medium">Amount</th>
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((e) => (
            <tr
              key={e.id}
              onClick={() => navigate(`/expenses/${e.id}`)}
              className="cursor-pointer border-b border-border last:border-0 hover:bg-accent"
            >
              <td className="px-3 py-2 text-muted-foreground">{e.expense_number}</td>
              <td className="px-3 py-2">{e.title}</td>
              <td className="px-3 py-2">{e.category_name || "—"}</td>
              <td className="px-3 py-2">{e.paid_by_name}</td>
              <td className="px-3 py-2 text-right">
                {e.currency} {e.amount}
              </td>
              <td className="px-3 py-2">{e.expense_date}</td>
              <td className="px-3 py-2 capitalize">{e.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
