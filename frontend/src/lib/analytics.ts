/** PostHog loads only after analytics consent, and only when a key is configured. */

export function loadAnalytics() {
  const key = import.meta.env.VITE_POSTHOG_KEY;
  if (!key || document.getElementById("posthog-loader")) return;
  const host = import.meta.env.VITE_POSTHOG_HOST || "https://us.i.posthog.com";
  const script = document.createElement("script");
  script.id = "posthog-loader";
  script.async = true;
  script.src = `${host}/static/array.js`;
  script.dataset.key = key;
  document.head.appendChild(script);
}

export function isFeatureEnabled(key: string, fallback = false) {
  const env = import.meta.env as Record<string, string | undefined>;
  const value = env[`VITE_FEATURE_${key.toUpperCase()}`];
  if (value === "true") return true;
  if (value === "false") return false;
  return fallback;
}
