import { useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { loadAnalytics } from "@/lib/analytics";

const STORAGE_KEY = "fn-cookie-consent";

export function CookieBanner() {
  const [open, setOpen] = useState(() => localStorage.getItem(STORAGE_KEY) === null);

  if (!open) return null;

  function choose(analytics: boolean) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ necessary: true, analytics, marketing: false })
    );
    if (analytics) loadAnalytics();
    setOpen(false);
  }

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed inset-x-4 bottom-4 z-50 rounded-lg border bg-background p-4 shadow-lg md:left-auto md:max-w-md"
    >
      <p className="text-sm">
        Necessary cookies keep you signed in. Analytics cookies are optional and load PostHog only
        after you accept. Read the <Link to="/legal/privacy">privacy notice</Link>.
      </p>
      <div className="mt-3 flex gap-2">
        <Button type="button" variant="outline" onClick={() => choose(false)}>
          Necessary only
        </Button>
        <Button type="button" onClick={() => choose(true)}>
          Accept analytics
        </Button>
      </div>
    </div>
  );
}
