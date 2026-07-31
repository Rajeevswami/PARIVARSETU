import { useState } from "react";

import { SearchInput } from "@/components/SearchInput";
import { useProfile } from "@/features/auth/hooks/useAuth";
import { CreateBorrowDialog } from "@/features/borrowLend/components/CreateBorrowDialog";
import { CreateLendDialog } from "@/features/borrowLend/components/CreateLendDialog";
import { SettlementDialog } from "@/features/borrowLend/components/SettlementDialog";
import { BorrowCard, LendCard } from "@/features/borrowLend/components/TransactionCard";
import {
  useBorrowTransactions,
  useLendTransactions,
} from "@/features/borrowLend/hooks/useBorrowLend";

export function BorrowLendPage() {
  const [tab, setTab] = useState<"borrow" | "lend">("borrow");
  const [search, setSearch] = useState("");
  const { data: currentUser } = useProfile();
  const isAdmin = currentUser?.role === "family_admin";

  const { data: borrowPage, isLoading: borrowLoading } = useBorrowTransactions({ search });
  const { data: lendPage, isLoading: lendLoading } = useLendTransactions({ search });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Borrow &amp; Lend</h1>
        {tab === "borrow" ? <CreateBorrowDialog /> : <CreateLendDialog />}
      </div>

      <div className="flex gap-2 border-b border-border">
        <button
          className={`px-3 py-2 text-sm ${tab === "borrow" ? "border-b-2 border-primary font-medium" : "text-muted-foreground"}`}
          onClick={() => setTab("borrow")}
        >
          Borrowed
        </button>
        <button
          className={`px-3 py-2 text-sm ${tab === "lend" ? "border-b-2 border-primary font-medium" : "text-muted-foreground"}`}
          onClick={() => setTab("lend")}
        >
          Lent
        </button>
      </div>

      <SearchInput placeholder="Search transactions…" onSearch={setSearch} />

      {tab === "borrow" ? (
        borrowLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="space-y-3">
            {(borrowPage?.data ?? []).map((t) => (
              <div key={t.id} className="space-y-2">
                <BorrowCard transaction={t} />
                {isAdmin && t.status !== "settled" && (
                  <SettlementDialog
                    referenceType="borrow"
                    referenceId={t.id}
                    memberId={t.borrower}
                    memberName={t.borrower_name}
                  />
                )}
              </div>
            ))}
            {borrowPage?.data.length === 0 && (
              <p className="text-sm text-muted-foreground">No borrow transactions yet.</p>
            )}
          </div>
        )
      ) : lendLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-3">
          {(lendPage?.data ?? []).map((t) => (
            <div key={t.id} className="space-y-2">
              <LendCard transaction={t} />
              {isAdmin && t.status !== "settled" && (
                <SettlementDialog
                  referenceType="lend"
                  referenceId={t.id}
                  memberId={t.receiver ?? t.giver}
                  memberName={t.receiver_name ?? t.giver_name}
                />
              )}
            </div>
          ))}
          {lendPage?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No lend transactions yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
