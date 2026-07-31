import { describe, expect, it } from "vitest";

import { createExpenseSchema, settlementSchema } from "@/features/expenses/schemas/expenseSchemas";

describe("createExpenseSchema", () => {
  const base = {
    title: "Groceries",
    expense_date: "2026-07-01",
    amount: "100.00",
    paid_by: "member-1",
    payment_method: "cash" as const,
    visibility: "family" as const,
    split_type: "equal" as const,
  };

  it("accepts a valid minimal payload", () => {
    expect(createExpenseSchema.safeParse(base).success).toBe(true);
  });

  it("rejects a blank title", () => {
    expect(createExpenseSchema.safeParse({ ...base, title: "" }).success).toBe(false);
  });

  it("rejects a zero amount", () => {
    expect(createExpenseSchema.safeParse({ ...base, amount: "0" }).success).toBe(false);
  });

  it("rejects a non-numeric amount", () => {
    expect(createExpenseSchema.safeParse({ ...base, amount: "abc" }).success).toBe(false);
  });

  it("rejects an invalid payment method", () => {
    expect(createExpenseSchema.safeParse({ ...base, payment_method: "bitcoin" }).success).toBe(
      false
    );
  });
});

describe("settlementSchema", () => {
  it("accepts a valid settlement", () => {
    const result = settlementSchema.safeParse({
      member_id: "member-1",
      paid_amount: "50.00",
      settlement_date: "2026-07-01",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a negative amount", () => {
    const result = settlementSchema.safeParse({
      member_id: "member-1",
      paid_amount: "-10",
      settlement_date: "2026-07-01",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing member", () => {
    const result = settlementSchema.safeParse({
      member_id: "",
      paid_amount: "50.00",
      settlement_date: "2026-07-01",
    });
    expect(result.success).toBe(false);
  });
});
