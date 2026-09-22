import { Link } from "react-router-dom";

const plans = [
  { name: "Free", price: "₹0", detail: "3 members, 1 household, 50 expenses a month" },
  { name: "Family", price: "₹499", detail: "15 members, 5 households, 2,000 expenses a month" },
  { name: "Premium", price: "₹1,499", detail: "Unlimited records and the ledger copilot" },
];

export function PricingPage() {
  return (
    <main id="main" className="mx-auto min-h-screen max-w-4xl px-6 py-16">
      <h1 className="text-3xl font-semibold">Pricing</h1>
      <p className="mt-2 text-muted-foreground">
        Prices are monthly, exclusive of tax, and shown again at checkout. This page is separate
        from the signed-in app.
      </p>
      <ul className="mt-8 grid gap-4 md:grid-cols-3">
        {plans.map((plan) => (
          <li key={plan.name} className="rounded-lg border p-4">
            <h2 className="text-lg font-medium">{plan.name}</h2>
            <p className="mt-2 text-2xl font-semibold">{plan.price}</p>
            <p className="mt-2 text-sm text-muted-foreground">{plan.detail}</p>
          </li>
        ))}
      </ul>
      <p className="mt-8 text-sm">
        <Link to="/welcome">Back</Link> · <Link to="/legal/terms">Terms</Link> ·{" "}
        <Link to="/legal/privacy">Privacy</Link>
      </p>
    </main>
  );
}
