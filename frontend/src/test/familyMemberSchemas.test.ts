import { describe, expect, it } from "vitest";

import { createFamilySchema } from "@/features/families/schemas/familySchemas";
import {
  acceptInvitationSchema,
  inviteMemberSchema,
} from "@/features/members/schemas/memberSchemas";

describe("createFamilySchema", () => {
  it("accepts a minimal valid payload", () => {
    expect(createFamilySchema.safeParse({ family_name: "Sharma Family" }).success).toBe(true);
  });

  it("rejects a blank family name", () => {
    expect(createFamilySchema.safeParse({ family_name: "" }).success).toBe(false);
  });
});

describe("inviteMemberSchema", () => {
  it("accepts an email-only invite", () => {
    const result = inviteMemberSchema.safeParse({ email: "a@b.com" });
    expect(result.success).toBe(true);
  });

  it("rejects an invite with neither email nor mobile", () => {
    const result = inviteMemberSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email format", () => {
    const result = inviteMemberSchema.safeParse({ email: "not-an-email" });
    expect(result.success).toBe(false);
  });
});

describe("acceptInvitationSchema", () => {
  it("accepts a valid name and strong password", () => {
    const result = acceptInvitationSchema.safeParse({
      first_name: "Rohan",
      password: "Str0ng!Pass1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a weak password", () => {
    const result = acceptInvitationSchema.safeParse({ first_name: "Rohan", password: "weak" });
    expect(result.success).toBe(false);
  });
});
