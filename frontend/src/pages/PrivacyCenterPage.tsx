import { useState } from "react";

import { api } from "@/api/axios";
import { Button } from "@/components/ui/button";

export function PrivacyCenterPage() {
  const [exportText, setExportText] = useState("");
  const [status, setStatus] = useState("");

  async function download() {
    const response = await api.post("/privacy/data-export/");
    setExportText(JSON.stringify(response.data.data, null, 2));
    setStatus("Export ready");
  }

  async function removeAccount() {
    await api.post("/privacy/deletion/", { confirm: true, reason: "requested from settings" });
    setStatus("Deletion requested");
  }

  return (
    <section className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Your data</h1>
      <p className="text-sm text-muted-foreground">
        Export is immediate. Deletion anonymises this login. Posted ledger rows may be retained
        where the law requires it.
      </p>
      <div className="flex gap-2">
        <Button type="button" onClick={() => void download()}>
          Export my data
        </Button>
        <Button type="button" variant="destructive" onClick={() => void removeAccount()}>
          Delete my account
        </Button>
      </div>
      {status ? <p>{status}</p> : null}
      {exportText ? (
        <pre className="max-h-80 overflow-auto rounded-md border p-3 text-xs">{exportText}</pre>
      ) : null}
    </section>
  );
}
