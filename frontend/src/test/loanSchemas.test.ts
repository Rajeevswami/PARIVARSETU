import { describe, expect, it } from "vitest";

import { createLoanSchema, recordPaymentSchema } from "@/features/loans/schemas/loanSchemas";
import {
  createBorrowSchema,
  settlementSchema,
} from "@/features/borrowLend/schemas/borrowLendSchemas";

describe("createLoanSchema", () => {
  const base = {
    title: "Car loan",
    borrower: "member-1",
    loan_source: "external" as const,
    external_lender_name: "ABC Bank",
    principal_amount: "10000.00",
    interest_type: "simple" as const,
    loan_date: "2026-01-01",
  };

  it("accepts a valid external loan", () => {
    expect(createLoanSchema.safeParse(base).success).toBe(true);
  });

  it("rejects an external loan with no lender name", () => {
    const result = createLoanSchema.safeParse({ ...base, external_lender_name: "" });
    expect(result.success).toBe(false);
  });

  it("rejects an internal loan with no lender", () => {
    const result = createLoanSchema.safeParse({
      ...base,
      loan_source: "internal",
      external_lender_name: "",
    });
    expect(result.success).toBe(false);
  });

  it("accepts an internal loan with a lender", () => {
    const result = createLoanSchema.safeParse({
      ...base,
      loan_source: "internal",
      lender: "member-2",
      external_lender_name: "",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a zero principal amount", () => {
    const result = createLoanSchema.safeParse({ ...base, principal_amount: "0" });
    expect(result.success).toBe(false);
  });
});

describe("recordPaymentSchema", () => {
  it("accepts a valid payment", () => {
    const result = recordPaymentSchema.safeParse({
      amount: "500.00",
      payment_date: "2026-02-01",
      payment_method: "cash",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a negative amount", () => {
    const result = recordPaymentSchema.safeParse({
      amount: "-50",
      payment_date: "2026-02-01",
      payment_method: "cash",
    });
    expect(result.success).toBe(false);
  });
});

describe("createBorrowSchema", () => {
  it("requires either a lender or an external lender name", () => {
    const result = createBorrowSchema.safeParse({
      borrower: "member-1",
      amount: "500.00",
      date: "2026-01-01",
      payment_method: "cash",
    });
    expect(result.success).toBe(false);
  });

  it("accepts with an external lender name", () => {
    const result = createBorrowSchema.safeParse({
      borrower: "member-1",
      external_lender_name: "Friend",
      amount: "500.00",
      date: "2026-01-01",
      payment_method: "cash",
    });
    expect(result.success).toBe(true);
  });
});

describe("settlementSchema", () => {
  it("accepts a valid settlement", () => {
    const result = settlementSchema.safeParse({
      member_id: "member-1",
      amount: "100.00",
      settlement_date: "2026-01-01",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a zero amount", () => {
    const result = settlementSchema.safeParse({
      member_id: "member-1",
      amount: "0",
      settlement_date: "2026-01-01",
    });
    expect(result.success).toBe(false);
  });
});
