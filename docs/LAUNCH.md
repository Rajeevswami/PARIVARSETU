# Launch checks

## Feature flags

`apps.common.features.is_enabled` reads `FEATURE_<KEY>`, then a platform row, then a family row, then the default. The browser equivalent is `VITE_FEATURE_<KEY>` in `frontend/src/lib/analytics.ts`.

## Analytics

PostHog is not loaded until the cookie banner records analytics consent, and only if `VITE_POSTHOG_KEY` is set. Necessary cookies remain available without that choice.

## Landing and pricing

`/welcome` and `/pricing` are public and separate from the signed-in dashboard at `/`. Terms and privacy are `/legal/terms` and `/legal/privacy`.

## Load test

`loadtests/locustfile.py` hits health and the public schema. It is a smoke profile, not a capacity certificate. Run it against a staging host before a launch decision.

## End-to-end

`frontend/e2e/pricing.spec.ts` is the suite. It checks the public pricing page. `npx playwright test` builds the frontend and serves the preview. Install the Playwright browser with `npx playwright install chromium` on a network that can reach the Playwright CDN. If that download is blocked, set `CHROME_PATH` to a local Chromium binary and `LD_LIBRARY_PATH` to its NSS libraries. Unit tests cover the cookie banner without a browser.

## Keys

| Key | Launch | Stub |
| --- | --- | --- |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_FAMILY_PRICE_ID`, `STRIPE_PREMIUM_PRICE_ID` | Required only if checkout uses Stripe. | Leave blank. Checkout then returns `provider_not_configured`. Manual billing still works. |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Required only if checkout uses Razorpay. A plan also needs `razorpay_plan_id`. | Leave blank. Do not set both providers unless you intend to offer both. |
| `EMAIL_PROVIDER=sendgrid` and `SENDGRID_API_KEY` | Required for real mail if SendGrid is the chosen provider. Also set `DEFAULT_FROM_EMAIL`. | `EMAIL_PROVIDER=console` prints mail. Safe for development, not for a public launch. |
| `EMAIL_PROVIDER=ses` and `EMAIL_BACKEND` | Required for real mail if SES is the chosen provider. This repo does not define AWS keys. The Django SES backend reads its own credentials. | Same console stub. SendGrid and SES are alternatives, not both. |
| `ANTHROPIC_API_KEY` | Required only when a live Claude reply is a launch feature. | Empty key disables the HTTP call. Tests use a scripted transport. `FEATURE_AI_COPILOT=false` is the kill switch. |
| `VITE_POSTHOG_KEY` | Not required to launch. | Empty key does not load PostHog. `POSTHOG_API_KEY` is loaded in Django settings and is not called by application code. |
| `VITE_POSTHOG_HOST`, `POSTHOG_HOST` | Only if a PostHog key is set and the project is not on the US cloud. | Default `https://us.i.posthog.com` is fine. |

## Accessibility

The app shell has a skip link to `#main`, a `lang` attribute, and labelled navigation that already existed. This is not a completed WCAG audit.

## PWA

`frontend/public/manifest.webmanifest`, icons, and `sw.js` cache the shell. The service worker registers only in production builds.

## Security review

See [SECURITY_REVIEW.md](SECURITY_REVIEW.md). It records what was checked in this repository and what still needs an external review.
