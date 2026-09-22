import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/api/axios";
import { Button } from "@/components/ui/button";

type Plan = { code: string; name: string; price_inr_paise: number; ai_enabled: boolean };

export function BillingPage() {
  const plans = useQuery({
    queryKey: ["billing-plans"],
    queryFn: async () => {
      const response = await api.get("/billing/plans/");
      return response.data.data as {
        plans: Plan[];
        current: { code: string; status: string } | null;
      };
    },
  });
  const checkout = useMutation({
    mutationFn: async (planCode: string) => {
      const response = await api.post("/billing/checkout/", {
        plan_code: planCode,
        provider: "manual",
      });
      const checkoutId = response.data.data.checkout_id as string;
      await api.post("/billing/checkout/confirm/", { checkout_id: checkoutId });
    },
    onSuccess: () => plans.refetch(),
  });

  return (
    <section className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Billing</h1>
      <p className="text-sm text-muted-foreground">
        Current plan: {plans.data?.current?.code ?? "not set"} ({plans.data?.current?.status ?? "—"}
        )
      </p>
      <ul className="grid gap-3 md:grid-cols-3">
        {(plans.data?.plans ?? []).map((plan) => (
          <li key={plan.code} className="rounded-lg border p-4">
            <h2 className="font-medium">{plan.name}</h2>
            <p className="text-sm text-muted-foreground">₹{plan.price_inr_paise / 100}</p>
            <Button
              className="mt-3"
              type="button"
              disabled={checkout.isPending}
              onClick={() => checkout.mutate(plan.code)}
            >
              Choose {plan.name}
            </Button>
          </li>
        ))}
      </ul>
      {checkout.isError ? <p role="alert">Checkout could not be started.</p> : null}
    </section>
  );
}
