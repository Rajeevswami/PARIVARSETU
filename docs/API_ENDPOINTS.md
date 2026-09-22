# API Endpoints Overview

Full interactive docs (auto-generated from the code):

- OpenAPI schema: `GET /api/v1/schema/`
- Swagger UI: `GET /api/v1/docs/`
- Redoc: `GET /api/v1/redoc/`

Those three are public and unthrottled. Every other `/api/v1/` route is in
the schema. JSON success responses use `{success, message, data}` plus
optional pagination `meta`. File exports (`/export/`, `/download/`) and
`POST /api/v1/auth/token/refresh/` are not enveloped. Authenticated
operations use the `jwtAuth` bearer scheme.

## Auth (`/api/v1/auth/`) — Module 3

login/, logout/, logout-all/, forgot-password/, reset-password/,
change-password/, token/refresh/, profile/, profile/avatar/,
login-history/, members/<id>/{reset-password,deactivate,reactivate}/

## Families (`/api/v1/families/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/families/` | List — a normal user only ever sees their own family |
| POST | `/families/` | Create — only if the user has no family yet; creator becomes Family Admin |
| GET | `/families/<id>/` | Detail |
| PATCH | `/families/<id>/` | Update — family_admin only |
| GET | `/families/mine/` | Shortcut for the caller's own family |

## Households (`/api/v1/households/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/households/` | List — filter by `status`; search `household_name`/`household_code`/`address` |
| POST | `/households/` | Create — family_admin only |
| GET | `/households/<id>/` | Detail |
| PATCH | `/households/<id>/` | Update — family_admin only |
| DELETE | `/households/<id>/` | Deactivate (soft delete) — family_admin only |
| POST | `/households/<id>/change_head/` | Body: `{"member_id": "..."}` — family_admin only |

## Members (`/api/v1/members/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/members/` | List — filter by `household`, `status`, `gender`, `relationship`; search `display_name`/email/mobile/relationship; order by `created_at`/`display_name` |
| POST | `/members/` | Create a Member profile for an existing, family-less User — family_admin only |
| GET | `/members/<id>/` | Detail — self or family_admin |
| PATCH | `/members/<id>/` | Update — self (own profile) or family_admin (any member) |
| POST | `/members/<id>/transfer/` | Body: `{"household_id": "..."}` (or `null`) — family_admin only |

## Invitations (`/api/v1/members/invitations/`)

| Method | Path | Notes |
|---|---|---|
| GET | `/invitations/` | List sent invitations — family_admin only |
| POST | `/invitations/` | Send — body: `email` or `mobile`, optional `household`, `role`, `relationship` |
| POST | `/invitations/accept/` | Public. Body: `token`, plus `first_name`+`password` if the invitee has no account yet |
| POST | `/invitations/reject/` | Public. Body: `token` |

## Billing, privacy, and assistant

| Method | Path | Notes |
|---|---|---|
| GET | `/billing/plans/` | Catalog and the caller's current subscription |
| POST | `/billing/checkout/` | Body: `plan_code`, `provider` (`manual`, `stripe`, `razorpay`) |
| POST | `/billing/checkout/confirm/` | Manual provider only |
| POST | `/billing/webhooks/<provider>/` | Signed provider events. Public, signature required |
| GET | `/privacy/legal/<document>/` | Public `terms` or `privacy` draft |
| POST | `/privacy/data-export/` | Caller's own export |
| POST | `/privacy/deletion/` | Body: `confirm: true` |
| GET/POST | `/onboarding/` | Progress for the signed-in user |
| GET/POST | `/referrals/` | Own code, or redeem `{code}` |
| POST | `/assistant/copilot/` | Premium or `ai_copilot` flag. Body: `message`, `language` |
| GET | `/health/` | Public database and cache check |
| GET | `/metrics/` | Staff only |
| GET | `/administration/ops/` | Staff operations counts |

All list endpoints return the standard paginated envelope
(`success`/`message`/`data`/`meta`); all others return
`success`/`message`/`data`.
