import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useAddComment, useComments } from "../hooks/useExpenses";

export function CommentSection({ expenseId }: { expenseId: string }) {
  const [text, setText] = useState("");
  const { data: comments, isLoading } = useComments(expenseId);
  const addComment = useAddComment(expenseId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    addComment.mutate(text.trim(), { onSuccess: () => setText("") });
  };

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">Comments</h2>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-2">
          {(comments ?? []).map((c) => (
            <div key={c.id} className="rounded-md border border-border p-3 text-sm">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{c.member_name}</span>
                <span>{new Date(c.created_at).toLocaleString()}</span>
              </div>
              <p className="mt-1">{c.comment}</p>
            </div>
          ))}
          {comments?.length === 0 && (
            <p className="text-sm text-muted-foreground">No comments yet.</p>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          placeholder="Add a comment…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <Button type="submit" size="sm" disabled={addComment.isPending || !text.trim()}>
          Post
        </Button>
      </form>
    </div>
  );
}
