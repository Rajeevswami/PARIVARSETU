# SaaS core

FamilyNexus bills the existing family tenant. It does not add a second tenant model.

## Plans

| Product name | Billing code | `Family.subscription_plan` | Limits |
|---|---|---|---|
| Free | `free` | `free` | 3 members, 1 household, 50 expenses / month, no assistant |
| Family | `family` | `basic` | 15 members, 5 households, 2,000 expenses / month |
| Premium | `premium` | `premium` | Unlimited records, assistant enabled |

Prices in code: Family ₹499 / month, Premium ₹1,499 / month. Tax is added by the payment provider.

A family created with `Family.objects.create` has no `Subscription` row and stays unlimited. That keeps existing tests and imported data working. `create_family` attaches a free trial subscription.

Limits are enforced in `create_expense`, `create_household`, and `send_invitation`.

## Payments

`POST /api/v1/billing/checkout/` starts Stripe, Razorpay, or the manual provider. Stripe and Razorpay are called with `urllib` only when their keys are set. The manual provider is the development and test path: confirm with `POST /api/v1/billing/checkout/confirm/`.

Webhooks live at `POST /api/v1/billing/webhooks/<provider>/`. An empty webhook secret rejects the request. Event ids are stored, so retries are idempotent.

## Onboarding, referrals, mail

`GET/POST /api/v1/onboarding/` tracks family, household, plan, and legal steps.

`GET/POST /api/v1/referrals/` issues a code and applies 14 days to the redeemer's current period.

In-app notifications are always written. Email is sent when the recipient has email enabled. `EMAIL_PROVIDER=sendgrid` calls SendGrid. `ses` uses the configured Django email backend.

## Privacy

Public drafts: `GET /api/v1/privacy/legal/terms/` and `GET /api/v1/privacy/legal/privacy/`. They are product templates for counsel, not a finished legal opinion. Jurisdiction draft is Jaipur, Rajasthan, under Indian law, including the direction of the DPDP Act, 2023.

`POST /api/v1/privacy/data-export/` returns the caller's profile and expenses they created. `POST /api/v1/privacy/deletion/` anonymises the login. Cookie choices are `POST /api/v1/privacy/consent/`.

## Operations dashboard

`GET /api/v1/administration/ops/` is staff-only and returns family, user, subscription, failed payment, and deletion counts. It does not return another family's ledger.
