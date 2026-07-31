import { useState } from "react";

import { Pagination } from "@/components/Pagination";
import { SearchInput } from "@/components/SearchInput";
import { InviteMemberDialog } from "@/features/members/components/InviteMemberDialog";
import { MemberCard } from "@/features/members/components/MemberCard";
import { useMembers } from "@/features/members/hooks/useMembers";
import { RELATIONSHIP_OPTIONS } from "@/features/members/schemas/memberSchemas";

export function MemberDirectoryPage() {
  const [search, setSearch] = useState("");
  const [relationship, setRelationship] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useMembers({
    search,
    relationship: relationship || undefined,
    status: status || undefined,
    page,
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Members</h1>
        <InviteMemberDialog />
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="flex-1 min-w-[200px]">
          <SearchInput placeholder="Search members…" onSearch={setSearch} />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={relationship}
          onChange={(e) => setRelationship(e.target.value)}
        >
          <option value="">All relationships</option>
          {RELATIONSHIP_OPTIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-3">
          {(data?.data ?? []).map((member) => (
            <MemberCard key={member.id} member={member} />
          ))}
          {data?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No members found.</p>
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
