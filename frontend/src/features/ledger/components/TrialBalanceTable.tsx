import { useTrialBalance } from "../hooks/useLedger";

export function TrialBalanceTable() {
  const { data: trialBalance, isLoading } = useTrialBalance();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (!trialBalance) return null;

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Code</th>
              <th className="px-3 py-2 font-medium">Account</th>
              <th className="px-3 py-2 font-medium">Group</th>
              <th className="px-3 py-2 text-right font-medium">Debit</th>
              <th className="px-3 py-2 text-right font-medium">Credit</th>
            </tr>
          </thead>
          <tbody>
            {trialBalance.rows.map((row) => (
              <tr key={row.account_code} className="border-b border-border last:border-0">
                <td className="px-3 py-2 text-muted-foreground">{row.account_code}</td>
                <td className="px-3 py-2">{row.account_name}</td>
                <td className="px-3 py-2 text-muted-foreground">{row.account_group}</td>
                <td className="px-3 py-2 text-right">{row.balance}</td>
                <td className="px-3 py-2 text-right">{row.credit_balance}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-border font-medium">
              <td className="px-3 py-2" colSpan={3}>
                Total
              </td>
              <td className="px-3 py-2 text-right">{trialBalance.grand_debit}</td>
              <td className="px-3 py-2 text-right">{trialBalance.grand_credit}</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        {trialBalance.grand_debit === trialBalance.grand_credit
          ? "✓ Balanced"
          : "⚠ Out of balance — this should never happen"}
      </p>
    </div>
  );
}
