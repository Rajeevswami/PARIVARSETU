import { useState } from "react";

import { TrialBalanceTable } from "@/features/ledger/components/TrialBalanceTable";
import { useBankBook, useCashBook, useFamilySummary } from "@/features/ledger/hooks/useLedger";

function BookTable({
  book,
}: {
  book:
    | {
        account_name: string;
        entries: {
          transaction_date: string;
          debit: string;
          credit: string;
          closing_balance: string;
          remarks: string;
        }[];
      }
    | undefined;
}) {
  if (!book) return <p className="text-sm text-muted-foreground">Loading…</p>;
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 text-right font-medium">Debit</th>
            <th className="px-3 py-2 text-right font-medium">Credit</th>
            <th className="px-3 py-2 text-right font-medium">Balance</th>
            <th className="px-3 py-2 font-medium">Remarks</th>
          </tr>
        </thead>
        <tbody>
          {book.entries.map((e, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              <td className="px-3 py-2">{e.transaction_date}</td>
              <td className="px-3 py-2 text-right">{e.debit}</td>
              <td className="px-3 py-2 text-right">{e.credit}</td>
              <td className="px-3 py-2 text-right">{e.closing_balance}</td>
              <td className="px-3 py-2 text-muted-foreground">{e.remarks}</td>
            </tr>
          ))}
          {book.entries.length === 0 && (
            <tr>
              <td colSpan={5} className="px-3 py-4 text-center text-muted-foreground">
                No entries yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function TrialBalancePage() {
  const [tab, setTab] = useState<"trial" | "cash" | "bank" | "summary">("trial");
  const { data: cashBook } = useCashBook();
  const { data: bankBook } = useBankBook();
  const { data: summary } = useFamilySummary();

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <h1 className="text-2xl font-semibold">Financial Statements</h1>

      <div className="flex gap-2 border-b border-border">
        {(["trial", "cash", "bank", "summary"] as const).map((t) => (
          <button
            key={t}
            className={`px-3 py-2 text-sm capitalize ${
              tab === t ? "border-b-2 border-primary font-medium" : "text-muted-foreground"
            }`}
            onClick={() => setTab(t)}
          >
            {t === "trial"
              ? "Trial Balance"
              : t === "cash"
                ? "Cash Book"
                : t === "bank"
                  ? "Bank Book"
                  : "Summary"}
          </button>
        ))}
      </div>

      {tab === "trial" && <TrialBalanceTable />}
      {tab === "cash" && <BookTable book={cashBook} />}
      {tab === "bank" && <BookTable book={bankBook} />}
      {tab === "summary" && summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Family balance</p>
            <p className="text-xl font-semibold">{summary.family_balance}</p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Household balance</p>
            <p className="text-xl font-semibold">{summary.household_balance}</p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Income</p>
            <p className="text-xl font-semibold">{summary.income_expense.income}</p>
          </div>
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted-foreground">Expense</p>
            <p className="text-xl font-semibold">{summary.income_expense.expense}</p>
          </div>
        </div>
      )}
    </div>
  );
}
