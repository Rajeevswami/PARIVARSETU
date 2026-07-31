import { RemindersPanel } from "@/features/loans/components/RemindersPanel";

export function LoanRemindersPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-6 text-2xl font-semibold">Reminders</h1>
      <RemindersPanel />
    </div>
  );
}
