import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { AttachmentSection } from "@/features/expenses/components/AttachmentSection";
import { CommentSection } from "@/features/expenses/components/CommentSection";
import { EditExpenseForm } from "@/features/expenses/components/EditExpenseForm";
import { ExpenseTimeline } from "@/features/expenses/components/ExpenseTimeline";
import { SettlementDialog } from "@/features/expenses/components/SettlementDialog";
import { useCancelExpense, useExpense } from "@/features/expenses/hooks/useExpenses";
import { useProfile } from "@/features/auth/hooks/useAuth";

export function ExpenseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: expense, isLoading } = useExpense(id);
  const { data: currentUser } = useProfile();
  const cancelExpense = useCancelExpense();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  if (!expense) return null;

  const isAdmin = currentUser?.role === "family_admin";

  return (
    <div className="mx-auto max-w-2xl space-y-8 px-4 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{expense.title}</h1>
          <p className="text-sm text-muted-foreground">
            {expense.expense_number} · {expense.currency} {expense.amount} · {expense.status}
          </p>
        </div>
        {isAdmin && expense.status !== "cancelled" && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => cancelExpense.mutate(expense.id)}
            disabled={cancelExpense.isPending}
          >
            Cancel expense
          </Button>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Participants</h2>
        <div className="space-y-2">
          {expense.participants.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between rounded-md border border-border p-3 text-sm"
            >
              <span>{p.member_name}</span>
              <span className="text-muted-foreground">
                Share {p.share_amount} · Pending {p.pending_amount} · {p.status}
              </span>
            </div>
          ))}
        </div>
        {isAdmin && (
          <div className="mt-3">
            <SettlementDialog expense={expense} />
          </div>
        )}
      </div>

      <EditExpenseForm expense={expense} />

      <AttachmentSection expense={expense} />

      <CommentSection expenseId={expense.id} />

      <ExpenseTimeline expense={expense} />
    </div>
  );
}
