import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useProfile } from "@/features/auth/hooks/useAuth";
import { LoanTimeline } from "@/features/loans/components/LoanTimeline";
import { PaymentHistory } from "@/features/loans/components/PaymentHistory";
import { RecordPaymentDialog } from "@/features/loans/components/RecordPaymentDialog";
import { useCancelLoan, useLoan } from "@/features/loans/hooks/useLoans";

export function LoanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: loan, isLoading } = useLoan(id);
  const { data: currentUser } = useProfile();
  const cancelLoan = useCancelLoan();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!loan) return null;

  const isAdmin = currentUser?.role === "family_admin";

  return (
    <div className="mx-auto max-w-2xl space-y-8 px-4 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{loan.title}</h1>
          <p className="text-sm text-muted-foreground">
            {loan.loan_number} · {loan.total_amount} · {loan.status}
          </p>
          <p className="text-sm text-muted-foreground">
            {loan.borrower_name} ← {loan.lender_name || loan.external_lender_name}
          </p>
        </div>
        {isAdmin && loan.status !== "cancelled" && loan.status !== "completed" && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => cancelLoan.mutate(loan.id)}
            disabled={cancelLoan.isPending}
          >
            Cancel loan
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-lg border border-border p-4 text-sm sm:grid-cols-4">
        <div>
          <p className="text-muted-foreground">Principal</p>
          <p className="font-medium">{loan.principal_amount}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Interest</p>
          <p className="font-medium">
            {loan.interest_amount} ({loan.interest_type})
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">Paid</p>
          <p className="font-medium">{loan.paid_amount}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Remaining</p>
          <p className="font-medium">{loan.remaining_amount}</p>
        </div>
      </div>

      {isAdmin && <RecordPaymentDialog loan={loan} />}

      <PaymentHistory loan={loan} />
      <LoanTimeline loan={loan} />
    </div>
  );
}
