import type { Expense } from "@/types/expense";

interface TimelineEntry {
  id: string;
  label: string;
  detail: string;
  timestamp: string;
}

export function ExpenseTimeline({ expense }: { expense: Expense }) {
  const entries: TimelineEntry[] = [
    {
      id: `created-${expense.id}`,
      label: "Expense created",
      detail: `${expense.paid_by_name} logged ${expense.currency} ${expense.amount}`,
      timestamp: expense.created_at,
    },
    ...expense.settlements.map((s) => ({
      id: s.id,
      label: "Settlement recorded",
      detail: `${s.paid_amount} paid${s.remarks ? ` — ${s.remarks}` : ""}`,
      timestamp: s.created_at,
    })),
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">Timeline</h2>
      <ol className="space-y-3 border-l border-border pl-4">
        {entries.map((entry) => (
          <li key={entry.id} className="relative">
            <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-primary" />
            <p className="text-sm font-medium">{entry.label}</p>
            <p className="text-sm text-muted-foreground">{entry.detail}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(entry.timestamp).toLocaleString()}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}
