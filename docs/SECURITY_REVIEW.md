# Security review notes

This is a repository review, not a penetration test.

## Checked

- Payment webhooks fail closed when the signing secret is empty, and event ids are unique.
- Provider credentials in `ApplicationConfiguration` are encrypted at rest when `FIELD_ENCRYPTION_KEY` is set.
- Staff metrics and the operations dashboard are not public.
- Assistant tools query by the caller's `family_id`.
- Telegram and WhatsApp webhooks require a configured secret.
- Production settings keep secure cookies, HSTS, and `X-Frame-Options`. Sentry does not send default PII.
- Cookie analytics stay off until an explicit choice.

## Still open

- Counsel must replace the draft terms and privacy notice before production.
- Stripe and Razorpay live keys, webhook endpoints, and tax settings are not configured here.
- Volume encryption, backup retention, and restore drills are operator tasks.
- A third party should test tenant isolation against a populated production-like database.
- The service worker caches `GET /`. Do not cache authenticated API responses in a later change without an explicit allow-list.
