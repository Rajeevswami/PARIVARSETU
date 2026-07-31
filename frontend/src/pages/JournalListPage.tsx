import { useState } from "react";
import { Link } from "react-router-dom";

import { Pagination } from "@/components/Pagination";
import { SearchInput } from "@/components/SearchInput";
import { Button } from "@/components/ui/button";
import { JournalCard } from "@/features/ledger/components/JournalCard";
import { ManualJournalDialog } from "@/features/ledger/components/ManualJournalDialog";
import { useJournals } from "@/features/ledger/hooks/useLedger";

export function JournalListPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useJournals({ search, status: status || undefined, page });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Journals</h1>
        <div className="flex gap-2">
          <Link to="/ledger/trial-balance">
            <Button variant="outline">Trial balance</Button>
          </Link>
          <Link to="/ledger/accounts">
            <Button variant="outline">Chart of accounts</Button>
          </Link>
          <ManualJournalDialog />
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="min-w-[200px] flex-1">
          <SearchInput placeholder="Search journals…" onSearch={setSearch} />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="posted">Posted</option>
          <option value="reversed">Reversed</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-3">
          {(data?.data ?? []).map((journal) => (
            <JournalCard key={journal.id} journal={journal} />
          ))}
          {data?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No journals yet.</p>
          )}
        </div>
      )}

      {data?.meta && (
        <Pagination
          currentPage={data.meta.current_page}
          totalPages={data.meta.total_pages}
          hasNext={data.meta.has_next}
          hasPrevious={data.meta.has_previous}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
