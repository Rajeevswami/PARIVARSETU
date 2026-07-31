import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useCreateJournal, useLedgerAccounts } from "../hooks/useLedger";
import type { JournalLineInput } from "../api/ledgerApi";

const emptyLine = (): JournalLineInput => ({
  ledger_account: "",
  entry_type: "debit",
  amount: "",
  description: "",
});

export function ManualJournalDialog() {
  const [open, setOpen] = useState(false);
  const [journalDate, setJournalDate] = useState("");
  const [description, setDescription] = useState("");
  const [lines, setLines] = useState<JournalLineInput[]>([emptyLine(), emptyLine()]);
  const [formError, setFormError] = useState("");

  const { data: accounts } = useLedgerAccounts();
  const createJournal = useCreateJournal();

  const totalDebit = lines
    .filter((l) => l.entry_type === "debit")
    .reduce((sum, l) => sum + (Number(l.amount) || 0), 0);
  const totalCredit = lines
    .filter((l) => l.entry_type === "credit")
    .reduce((sum, l) => sum + (Number(l.amount) || 0), 0);
  const isBalanced = totalDebit === totalCredit && totalDebit > 0;

  const updateLine = (index: number, patch: Partial<JournalLineInput>) => {
    setLines((prev) => prev.map((l, i) => (i === index ? { ...l, ...patch } : l)));
  };

  const addLine = () => setLines((prev) => [...prev, emptyLine()]);
  const removeLine = (index: number) => setLines((prev) => prev.filter((_, i) => i !== index));

  const handleSubmit = () => {
    if (!journalDate) {
      setFormError("Journal date is required.");
      return;
    }
    if (lines.some((l) => !l.ledger_account || !l.amount)) {
      setFormError("Every line needs an account and an amount.");
      return;
    }
    if (!isBalanced) {
      setFormError(`Not balanced: debit ${totalDebit} ≠ credit ${totalCredit}.`);
      return;
    }
    setFormError("");

    createJournal.mutate(
      { journal_date: journalDate, description: description || undefined, lines },
      {
        onSuccess: () => {
          setJournalDate("");
          setDescription("");
          setLines([emptyLine(), emptyLine()]);
          setOpen(false);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>New manual journal</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New manual journal</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="journal_date">Date</Label>
              <Input
                id="journal_date"
                type="date"
                value={journalDate}
                onChange={(e) => setJournalDate(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Lines</Label>
            {lines.map((line, index) => (
              <div key={index} className="flex items-center gap-2">
                <select
                  className="h-9 flex-1 rounded-md border border-input bg-background px-2 text-sm shadow-sm"
                  value={line.ledger_account}
                  onChange={(e) => updateLine(index, { ledger_account: e.target.value })}
                >
                  <option value="">Account</option>
                  {(accounts ?? []).map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.account_code} — {a.account_name}
                    </option>
                  ))}
                </select>
                <select
                  className="h-9 w-24 rounded-md border border-input bg-background px-2 text-sm shadow-sm"
                  value={line.entry_type}
                  onChange={(e) =>
                    updateLine(index, { entry_type: e.target.value as "debit" | "credit" })
                  }
                >
                  <option value="debit">Debit</option>
                  <option value="credit">Credit</option>
                </select>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="Amount"
                  className="w-28"
                  value={line.amount}
                  onChange={(e) => updateLine(index, { amount: e.target.value })}
                />
                {lines.length > 2 && (
                  <Button type="button" variant="ghost" size="sm" onClick={() => removeLine(index)}>
                    ✕
                  </Button>
                )}
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={addLine}>
              Add line
            </Button>
          </div>

          <p className={`text-sm ${isBalanced ? "text-muted-foreground" : "text-destructive"}`}>
            Debit {totalDebit.toFixed(2)} · Credit {totalCredit.toFixed(2)}
          </p>

          {(formError || createJournal.isError) && (
            <p className="text-sm text-destructive">
              {formError || "Could not create the journal."}
            </p>
          )}

          <Button onClick={handleSubmit} className="w-full" disabled={createJournal.isPending}>
            {createJournal.isPending ? "Saving…" : "Create journal (draft)"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
