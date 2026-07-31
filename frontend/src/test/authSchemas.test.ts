import { describe, expect, it } from "vitest";

import {
  changePasswordSchema,
  loginSchema,
  resetPasswordSchema,
} from "@/features/auth/schemas/authSchemas";

describe("authSchemas", () => {
  it("accepts a valid login payload", () => {
    const result = loginSchema.safeParse({ identifier: "a@b.com", password: "x" });
    expect(result.success).toBe(true);
  });

  it("rejects an empty identifier", () => {
    const result = loginSchema.safeParse({ identifier: "", password: "x" });
    expect(result.success).toBe(false);
  });

  it("rejects a password missing complexity requirements", () => {
    const result = resetPasswordSchema.safeParse({
      newPassword: "weak",
      confirmPassword: "weak",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a strong matching password pair", () => {
    const result = resetPasswordSchema.safeParse({
      newPassword: "Str0ng!Pass1",
      confirmPassword: "Str0ng!Pass1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects change-password when new equals old", () => {
    const result = changePasswordSchema.safeParse({
      oldPassword: "Str0ng!Pass1",
      newPassword: "Str0ng!Pass1",
      confirmPassword: "Str0ng!Pass1",
    });
    expect(result.success).toBe(false);
  });
});
