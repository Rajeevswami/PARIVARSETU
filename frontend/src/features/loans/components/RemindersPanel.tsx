import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

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
import { useMembers } from "@/features/members/hooks/useMembers";

import { useCreateReminder, useDismissReminder, useReminders } from "../hooks/useLoans";
import { reminderSchema, type ReminderFormValues } from "../schemas/loanSchemas";

export function RemindersPanel() {
  const [open, setOpen] = useState(false);
  const { data: reminders, isLoading } = useReminders();
  const { data: membersPage } = useMembers();
  const createReminder = useCreateReminder();
  const dismissReminder = useDismissReminder();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReminderFormValues>({
    resolver: zodResolver(reminderSchema),
    defaultValues: { reminder_type: "custom" },
  });

  const onSubmit = (values: ReminderFormValues) =>
    createReminder.mutate(
      {
        member: values.member,
        loan: values.loan || undefined,
        reminder_type: values.reminder_type,
        title: values.title,
        message: values.message || undefined,
        remind_at: values.remind_at,
      },
      {
        onSuccess: () => {
          reset();
          setOpen(false);
        },
      }
    );

  const pending = (reminders ?? []).filter((r) => r.status === "pending");

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Reminders</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              New reminder
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New reminder</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="member">For</Label>
                <select
                  id="member"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                  {...register("member")}
                >
                  <option value="">Select member</option>
                  {(membersPage?.data ?? []).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.display_name}
                    </option>
                  ))}
                </select>
                {errors.member && (
                  <p className="text-sm text-destructive">{errors.member.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="title">Title</Label>
                <Input id="title" {...register("title")} />
                {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="remind_at">Remind at</Label>
                <Input id="remind_at" type="datetime-local" {...register("remind_at")} />
                {errors.remind_at && (
                  <p className="text-sm text-destructive">{errors.remind_at.message}</p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={createReminder.isPending}>
                {createReminder.isPending ? "Saving…" : "Create reminder"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-2">
          {pending.map((r) => (
            <div
              key={r.id}
              className="flex items-center justify-between rounded-md border border-border p-3 text-sm"
            >
              <div>
                <p className="font-medium">{r.title}</p>
                <p className="text-xs text-muted-foreground">
                  {r.member_name} · {new Date(r.remind_at).toLocaleString()}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => dismissReminder.mutate(r.id)}>
                Dismiss
              </Button>
            </div>
          ))}
          {pending.length === 0 && (
            <p className="text-sm text-muted-foreground">No pending reminders.</p>
          )}
        </div>
      )}
    </div>
  );
}
