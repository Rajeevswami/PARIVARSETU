import type { Loan } from "@/types/loan";

export function PaymentHistory({ loan }: { loan: Loan }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">Payment history</h2>
      <div className="space-y-2">
        {loan.payments.map((p) => (
          <div key={p.id} className="rounded-md border border-border p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">{p.amount}</span>
              <span className="text-muted-foreground">{p.payment_date}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Interest {p.interest_paid} · Principal {p.principal_paid} · Balance after:{" "}
              {p.remaining_balance}
            </p>
            {p.remarks && <p className="mt-1 text-xs text-muted-foreground">{p.remarks}</p>}
          </div>
        ))}
        {loan.payments.length === 0 && (
          <p className="text-sm text-muted-foreground">No payments yet.</p>
        )}
      </div>
    </div>
  );
}
