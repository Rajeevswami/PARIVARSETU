import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { SignupPage } from "@/pages/SignupPage";
import { LandingPage } from "@/pages/LandingPage";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe("SignupPage", () => {
  it("shows validation errors when submitted empty", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SignupPage />);

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/enter a valid email address/i)).toBeInTheDocument();
    expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
  });

  it("rejects a password confirmation that does not match", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SignupPage />);

    await user.type(screen.getByLabelText(/^name$/i), "Asha Sharma");
    await user.type(screen.getByLabelText(/^email$/i), "asha@familynexus.app");
    await user.type(screen.getByLabelText(/^password$/i), "Str0ng!Pass1");
    await user.type(screen.getByLabelText(/^confirm password$/i), "Str0ng!Pass2");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
  });
});

describe("signup links", () => {
  it("links from login and the welcome page", () => {
    renderWithProviders(
      <>
        <LandingPage />
        <LoginForm />
      </>
    );
    const links = screen.getAllByRole("link", { name: /create an account|create account/i });
    expect(links.length).toBeGreaterThanOrEqual(2);
    expect(links.every((link) => link.getAttribute("href") === "/signup")).toBe(true);
  });
});
