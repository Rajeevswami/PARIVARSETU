import { LayoutGrid, Table as TableIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Pagination } from "@/components/Pagination";
import { SearchInput } from "@/components/SearchInput";
import { Button } from "@/components/ui/button";
import { CreateExpenseDialog } from "@/features/expenses/components/CreateExpenseDialog";
import { ExpenseCard } from "@/features/expenses/components/ExpenseCard";
import { ExpenseTable } from "@/features/expenses/components/ExpenseTable";
import { StatsWidget } from "@/features/expenses/components/StatsWidget";
import { useCategories, useExpenses } from "@/features/expenses/hooks/useExpenses";

export function ExpenseListPage() {
  const [view, setView] = useState<"card" | "table">("card");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [ordering, setOrdering] = useState("-expense_date");
  const [page, setPage] = useState(1);

  const params = {
    search,
    status: status || undefined,
    category: category || undefined,
    ordering,
    page,
  };
  const { data, isLoading } = useExpenses(params);
  const { data: categories } = useCategories();

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Expenses</h1>
        <div className="flex gap-2">
          <Link to="/expenses/categories">
            <Button variant="outline">Categories</Button>
          </Link>
          <CreateExpenseDialog />
        </div>
      </div>

      <StatsWidget params={params} />

      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-[200px] flex-1">
          <SearchInput placeholder="Search expenses…" onSearch={setSearch} />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="settled">Settled</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {(categories ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={ordering}
          onChange={(e) => setOrdering(e.target.value)}
        >
          <option value="-expense_date">Newest</option>
          <option value="expense_date">Oldest</option>
          <option value="-amount">Highest amount</option>
          <option value="amount">Lowest amount</option>
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
          {(data?.data ?? []).map((expense) => (
            <ExpenseCard key={expense.id} expense={expense} />
          ))}
          {data?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No expenses found.</p>
          )}
        </div>
      ) : (
        <ExpenseTable expenses={data?.data ?? []} />
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
