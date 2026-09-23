import axios from "axios";
import { useState } from "react";

import { api } from "@/api/axios";
import { Button } from "@/components/ui/button";
import { isFeatureEnabled } from "@/lib/analytics";

export function AssistantPage() {
  const [message, setMessage] = useState("Summarise this month");
  const [reply, setReply] = useState("");
  const [error, setError] = useState("");
  const enabled = isFeatureEnabled("AI_COPILOT", true);

  async function ask() {
    setError("");
    try {
      const response = await api.post("/assistant/copilot/", { message, language: "en" });
      setReply(response.data.data.message as string);
    } catch (caught) {
      const message = axios.isAxiosError(caught)
        ? (caught.response?.data as { message?: string } | undefined)?.message
        : undefined;
      setError(message || "The assistant is unavailable on this plan.");
    }
  }

  return (
    <section className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Ledger copilot</h1>
      <p className="text-sm text-muted-foreground">
        Numbers come from family tools. The assistant does not invent balances.
      </p>
      {enabled ? (
        <>
          <label className="block text-sm" htmlFor="copilot-message">
            Question
            <textarea
              id="copilot-message"
              className="mt-1 w-full rounded-md border p-2"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />
          </label>
          <Button type="button" onClick={() => void ask()}>
            Ask
          </Button>
          {reply ? <p>{reply}</p> : null}
          {error ? <p role="alert">{error}</p> : null}
        </>
      ) : (
        <p>The copilot flag is off for this browser.</p>
      )}
    </section>
  );
}
