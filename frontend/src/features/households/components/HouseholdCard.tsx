import { Link } from "react-router-dom";

import type { Household } from "@/types/household";

export function HouseholdCard({ household }: { household: Household }) {
  return (
    <Link
      to={`/households/${household.id}`}
      className="block rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{household.household_name}</h3>
        <span className="text-xs text-muted-foreground">{household.household_code}</span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {household.member_count} member{household.member_count === 1 ? "" : "s"}
        {household.head_of_household_name && ` · Head: ${household.head_of_household_name}`}
      </p>
      {household.address && (
        <p className="mt-1 text-sm text-muted-foreground">{household.address}</p>
      )}
    </Link>
  );
}
