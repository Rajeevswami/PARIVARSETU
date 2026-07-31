import { useExpenseStats } from "../hooks/useExpenses";
import type { ExpenseListParams } from "../api/expensesApi";

export function StatsWidget({ params = {} }: { params?: ExpenseListParams }) {
  const { data: stats, isLoading } = useExpenseStats(params);

  if (isLoading || !stats) return null;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div className="rounded-lg border border-border p-4">
        <p className="text-xs text-muted-foreground">Total</p>
        <p className="text-xl font-semibold">{stats.grand_total}</p>
      </div>
      {stats.by_status.slice(0, 3).map((s) => (
        <div key={s.status} className="rounded-lg border border-border p-4">
          <p className="text-xs capitalize text-muted-foreground">{s.status}</p>
          <p className="text-xl font-semibold">{s.total}</p>
          <p className="text-xs text-muted-foreground">{s.count} expense(s)</p>
        </div>
      ))}
    </div>
  );
}
