import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "@/App";

describe("App", () => {
  it("redirects to the login page when there is no session", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "ParivarSetu" })).toBeInTheDocument();
    expect(screen.getByText(/Sign in to your family's account/i)).toBeInTheDocument();
  });
});
