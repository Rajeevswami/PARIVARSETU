import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { APP_NAME } from "@/constants";

export function LandingPage() {
  return (
    <main id="main" className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-6">
      <p className="text-sm font-medium text-muted-foreground">{APP_NAME}</p>
      <h1 className="text-4xl font-semibold tracking-tight">A shared ledger for the whole family.</h1>
      <p className="text-lg text-muted-foreground">
        Expenses, loans, and documents stay inside one family tenant. Free, Family, and Premium
        plans are billed in India through Razorpay or internationally through Stripe.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link to="/login">Sign in</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/pricing">See pricing</Link>
        </Button>
      </div>
    </main>
  );
}
