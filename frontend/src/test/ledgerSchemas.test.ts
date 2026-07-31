import { describe, expect, it } from "vitest";

import { createAccountSchema, createJournalSchema } from "@/features/ledger/schemas/ledgerSchemas";

describe("createJournalSchema", () => {
  const base = {
    journal_date: "2026-01-01",
    lines: [
      { ledger_account: "acc-1", entry_type: "debit" as const, amount: "100.00" },
      { ledger_account: "acc-2", entry_type: "credit" as const, amount: "100.00" },
    ],
  };

  it("accepts a valid two-line journal", () => {
    expect(createJournalSchema.safeParse(base).success).toBe(true);
  });

  it("rejects a journal with fewer than two lines", () => {
    const result = createJournalSchema.safeParse({ ...base, lines: [base.lines[0]] });
    expect(result.success).toBe(false);
  });

  it("rejects a line with a zero amount", () => {
    const result = createJournalSchema.safeParse({
      ...base,
      lines: [
        { ledger_account: "acc-1", entry_type: "debit" as const, amount: "0" },
        { ledger_account: "acc-2", entry_type: "credit" as const, amount: "0" },
      ],
    });
    expect(result.success).toBe(false);
  });

  it("rejects a line missing an account", () => {
    const result = createJournalSchema.safeParse({
      ...base,
      lines: [
        { ledger_account: "", entry_type: "debit" as const, amount: "10" },
        { ledger_account: "acc-2", entry_type: "credit" as const, amount: "10" },
      ],
    });
    expect(result.success).toBe(false);
  });
});

describe("createAccountSchema", () => {
  it("accepts a valid account", () => {
    const result = createAccountSchema.safeParse({
      account_code: "1099",
      account_name: "Petty Cash",
      account_group: "group-1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a blank account code", () => {
    const result = createAccountSchema.safeParse({
      account_code: "",
      account_name: "Petty Cash",
      account_group: "group-1",
    });
    expect(result.success).toBe(false);
  });
});
