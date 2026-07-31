import { LayoutGrid, Table as TableIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Pagination } from "@/components/Pagination";
import { SearchInput } from "@/components/SearchInput";
import { Button } from "@/components/ui/button";
import { CreateLoanDialog } from "@/features/loans/components/CreateLoanDialog";
import { LoanCard } from "@/features/loans/components/LoanCard";
import { LoanStatsWidget } from "@/features/loans/components/LoanStatsWidget";
import { LoanTable } from "@/features/loans/components/LoanTable";
import { useLoans } from "@/features/loans/hooks/useLoans";

export function LoanListPage() {
  const [view, setView] = useState<"card" | "table">("card");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [ordering, setOrdering] = useState("-loan_date");
  const [page, setPage] = useState(1);

  const params = { search, status: status || undefined, ordering, page };
  const { data, isLoading } = useLoans(params);

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Loans</h1>
        <div className="flex gap-2">
          <Link to="/loans/reminders">
            <Button variant="outline">Reminders</Button>
          </Link>
          <CreateLoanDialog />
        </div>
      </div>

      <LoanStatsWidget params={params} />

      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-[200px] flex-1">
          <SearchInput placeholder="Search loans…" onSearch={setSearch} />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="defaulted">Defaulted</option>
        </select>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={ordering}
          onChange={(e) => setOrdering(e.target.value)}
        >
          <option value="-loan_date">Newest</option>
          <option value="loan_date">Oldest</option>
          <option value="-total_amount">Highest amount</option>
          <option value="total_amount">Lowest amount</option>
          <option value="title">Alphabetical</option>
        </select>
        <div className="ml-auto flex gap-1">
          <Button
            variant={view === "card" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setView("card")}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={view === "table" ? "secondary" : "ghost"}
            size="icon"
            onClick={() => setView("table")}
          >
            <TableIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : view === "card" ? (
        <div className="space-y-3">
          {(data?.data ?? []).map((loan) => (
            <LoanCard key={loan.id} loan={loan} />
          ))}
          {data?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No loans found.</p>
          )}
        </div>
      ) : (
        <LoanTable loans={data?.data ?? []} />
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
