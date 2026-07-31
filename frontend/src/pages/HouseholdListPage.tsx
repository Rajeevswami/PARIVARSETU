import { useState } from "react";

import { Pagination } from "@/components/Pagination";
import { SearchInput } from "@/components/SearchInput";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { HouseholdCard } from "@/features/households/components/HouseholdCard";
import { HouseholdForm } from "@/features/households/components/HouseholdForm";
import { useHouseholds } from "@/features/households/hooks/useHouseholds";

export function HouseholdListPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const { data, isLoading } = useHouseholds({ search, page });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Households</h1>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>New household</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create household</DialogTitle>
            </DialogHeader>
            <HouseholdForm onDone={() => setCreateOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      <SearchInput placeholder="Search households…" onSearch={setSearch} />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-3">
          {(data?.data ?? []).map((household) => (
            <HouseholdCard key={household.id} household={household} />
          ))}
          {data?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No households yet.</p>
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
