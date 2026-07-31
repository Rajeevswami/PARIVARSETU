import { Search } from "lucide-react";
import { useState } from "react";

import { Input } from "@/components/ui/input";

export function SearchInput({
  placeholder = "Search…",
  onSearch,
}: {
  placeholder?: string;
  onSearch: (value: string) => void;
}) {
  const [value, setValue] = useState("");

  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        placeholder={placeholder}
        className="pl-8"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          onSearch(e.target.value);
        }}
      />
    </div>
  );
}
