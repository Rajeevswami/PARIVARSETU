import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useJournal, usePostJournal } from "@/features/ledger/hooks/useLedger";

export function JournalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: journal, isLoading } = useJournal(id);
  const postJournal = usePostJournal();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!journal) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{journal.journal_number}</h1>
          <p className="text-sm text-muted-foreground">
            {journal.transaction_type} · {journal.journal_date} · {journal.status}
          </p>
          {journal.description && (
            <p className="text-sm text-muted-foreground">{journal.description}</p>
          )}
        </div>
        {journal.status === "draft" && (
          <Button
            size="sm"
            onClick={() => postJournal.mutate(journal.id)}
            disabled={postJournal.isPending}
          >
            {postJournal.isPending ? "Posting…" : "Post journal"}
          </Button>
        )}
      </div>

      {postJournal.isError && (
        <p className="text-sm text-destructive">
          {(postJournal.error as { response?: { data?: { message?: string } } })?.response?.data
            ?.message ?? "Could not post this journal."}
        </p>
      )}

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Account</th>
              <th className="px-3 py-2 font-medium">Type</th>
              <th className="px-3 py-2 text-right font-medium">Amount</th>
              <th className="px-3 py-2 font-medium">Description</th>
            </tr>
          </thead>
          <tbody>
            {journal.entries.map((entry) => (
              <tr key={entry.id} className="border-b border-border last:border-0">
                <td className="px-3 py-2">{entry.ledger_account_name}</td>
                <td className="px-3 py-2 capitalize">{entry.entry_type}</td>
                <td className="px-3 py-2 text-right">{entry.amount}</td>
                <td className="px-3 py-2 text-muted-foreground">{entry.description}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-border font-medium">
              <td className="px-3 py-2" colSpan={2}>
                Total
              </td>
              <td className="px-3 py-2 text-right">
                Dr {journal.total_debit} / Cr {journal.total_credit}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
