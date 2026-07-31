import { useState } from "react";

import { SearchInput } from "@/components/SearchInput";
import { CreateAccountDialog } from "@/features/ledger/components/CreateAccountDialog";
import { useLedgerAccounts } from "@/features/ledger/hooks/useLedger";

export function ChartOfAccountsPage() {
  const [search, setSearch] = useState("");
  const { data: accounts, isLoading } = useLedgerAccounts(search);

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Chart of Accounts</h1>
        <CreateAccountDialog />
      </div>

      <SearchInput placeholder="Search accounts…" onSearch={setSearch} />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Group</th>
                <th className="px-3 py-2 text-right font-medium">Balance</th>
                <th className="px-3 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {(accounts ?? []).map((a) => (
                <tr key={a.id} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 text-muted-foreground">{a.account_code}</td>
                  <td className="px-3 py-2">
                    {a.account_name}
                    {a.is_system_account && (
                      <span className="ml-2 text-xs text-muted-foreground">(system)</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{a.account_group_name}</td>
                  <td className="px-3 py-2 text-right">{a.current_balance}</td>
                  <td className="px-3 py-2 capitalize">{a.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
