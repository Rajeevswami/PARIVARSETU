import { beforeEach, describe, expect, it } from "vitest";

import { migrateLegacyStorage } from "@/lib/migrateLegacyStorage";

describe("migrateLegacyStorage", () => {
  beforeEach(() => localStorage.clear());

  it("copies legacy keys once and does not overwrite a newer value", () => {
    localStorage.setItem("parivarsetu_access_token", "old-refresh");
    localStorage.setItem("parivarsetu-theme", "dark");

    migrateLegacyStorage();

    expect(localStorage.getItem("familynexus_access_token")).toBe("old-refresh");
    expect(localStorage.getItem("familynexus-theme")).toBe("dark");
    expect(localStorage.getItem("parivarsetu_access_token")).toBeNull();
    expect(localStorage.getItem("parivarsetu-theme")).toBeNull();

    localStorage.setItem("parivarsetu_access_token", "stale");
    migrateLegacyStorage();
    expect(localStorage.getItem("familynexus_access_token")).toBe("old-refresh");
    expect(localStorage.getItem("parivarsetu_access_token")).toBeNull();
  });
});
