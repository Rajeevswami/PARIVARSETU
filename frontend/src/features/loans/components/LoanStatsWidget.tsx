import { useLoanStats } from "../hooks/useLoans";
import type { LoanListParams } from "../api/loansApi";

export function LoanStatsWidget({ params = {} }: { params?: LoanListParams }) {
  const { data: stats, isLoading } = useLoanStats(params);

  if (isLoading || !stats) return null;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div className="rounded-lg border border-border p-4">
        <p className="text-xs text-muted-foreground">Total loans</p>
        <p className="text-xl font-semibold">{stats.grand_total}</p>
      </div>
      <div className="rounded-lg border border-border p-4">
        <p className="text-xs text-muted-foreground">Outstanding</p>
        <p className="text-xl font-semibold">{stats.outstanding_total}</p>
      </div>
      {stats.by_status.slice(0, 2).map((s) => (
        <div key={s.status} className="rounded-lg border border-border p-4">
          <p className="text-xs capitalize text-muted-foreground">{s.status}</p>
          <p className="text-xl font-semibold">{s.total}</p>
          <p className="text-xs text-muted-foreground">{s.count} loan(s)</p>
        </div>
      ))}
    </div>
  );
}
