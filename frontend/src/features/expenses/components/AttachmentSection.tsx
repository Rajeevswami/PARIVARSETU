import { useRef } from "react";

import { Button } from "@/components/ui/button";
import type { Expense } from "@/types/expense";

import { useUploadAttachment } from "../hooks/useExpenses";

export function AttachmentSection({ expense }: { expense: Expense }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAttachment = useUploadAttachment(expense.id);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadAttachment.mutate(file);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Bills &amp; receipts</h2>
        <input
          ref={inputRef}
          type="file"
          accept="image/*,.pdf"
          className="hidden"
          onChange={handleFileChange}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => inputRef.current?.click()}
          disabled={uploadAttachment.isPending}
        >
          {uploadAttachment.isPending ? "Uploading…" : "Upload"}
        </Button>
      </div>

      <div className="space-y-2">
        {expense.attachments.map((a) => (
          <a
            key={a.id}
            href={a.file}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between rounded-md border border-border p-2 text-sm hover:bg-accent"
          >
            <span>{a.file_name}</span>
            <span className="text-xs text-muted-foreground">
              {(a.file_size / 1024).toFixed(0)} KB
            </span>
          </a>
        ))}
        {expense.attachments.length === 0 && (
          <p className="text-sm text-muted-foreground">No attachments yet.</p>
        )}
      </div>
    </div>
  );
}
