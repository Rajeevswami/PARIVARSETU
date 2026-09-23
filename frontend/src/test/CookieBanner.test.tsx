import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { CookieBanner } from "@/components/CookieBanner";

describe("CookieBanner", () => {
  it("stores a necessary-only choice", async () => {
    localStorage.removeItem("fn-cookie-consent");
    render(
      <MemoryRouter>
        <CookieBanner />
      </MemoryRouter>
    );
    await userEvent.click(screen.getByRole("button", { name: "Necessary only" }));
    expect(localStorage.getItem("fn-cookie-consent")).toContain('"analytics":false');
    expect(screen.queryByRole("dialog", { name: "Cookie consent" })).not.toBeInTheDocument();
  });
});
