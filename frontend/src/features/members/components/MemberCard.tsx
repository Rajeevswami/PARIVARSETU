import { Link } from "react-router-dom";

import type { Member } from "@/types/member";

export function MemberCard({ member }: { member: Member }) {
  return (
    <Link
      to={`/members/${member.id}`}
      className="block rounded-lg border border-border p-4 transition-colors hover:bg-accent"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{member.display_name}</h3>
        <span
          className={`text-xs ${member.status === "active" ? "text-muted-foreground" : "text-destructive"}`}
        >
          {member.status}
        </span>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {member.relationship || "Relationship not set"}
        {member.household_name && ` · ${member.household_name}`}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{member.email}</p>
    </Link>
  );
}
