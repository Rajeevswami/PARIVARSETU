import { Link } from "react-router-dom";

import type { Journal } from "@/types/ledger";

const STATUS_COLOR: Record<string, string> = {
  draft: "text-amber-600 dark:text-amber-400",
  posted: "text-green-600 dark:text-green-400",
  reversed: "text-destructive",
};

export function JournalCard({ journal }: { journal: Journal }) {
  return (
    <Link
      to={`/ledger/journals/${journal.id}`}
      className="block rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{journal.journal_number}</h3>
        <span className={STATUS_COLOR[journal.status]}>{journal.status}</span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {journal.transaction_type} · {journal.journal_date}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Dr {journal.total_debit} · Cr {journal.total_credit}
      </p>
      {journal.description && (
        <p className="mt-1 text-xs text-muted-foreground">{journal.description}</p>
      )}
    </Link>
  );
}
