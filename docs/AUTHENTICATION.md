# Authentication Guide

## Login

`POST /api/v1/auth/login/`

Accepts **either** an email or a mobile number in `identifier` — the same
endpoint handles both, resolved by a single lookup
(`Q(email__iexact=identifier) | Q(mobile=identifier)`).

```json
{ "identifier": "user@parivarsetu.app", "password": "Str0ng!Pass1" }
```

Returns `{ user, tokens: { access, refresh } }` on success. Rejects:
deleted accounts (`account_deleted`, 403), inactive/blocked/pending
accounts (`account_inactive`, 403), and wrong credentials
(`invalid_credentials`, 401) — every failure is written to the audit log.

## Tokens

- Access token: 15 minutes. Refresh token: 7 days, **rotated** on every
  use, and the old one is blacklisted (`ROTATE_REFRESH_TOKENS` +
  `BLACKLIST_AFTER_ROTATION` in settings).
- `POST /api/v1/auth/token/refresh/` — standard Simple JWT refresh.
- `POST /api/v1/auth/logout/` — blacklists the given refresh token.
- `POST /api/v1/auth/logout-all/` — blacklists every outstanding token
  for the current user (all devices/sessions).

Frontend: the access token lives in memory only; the refresh token is in
`localStorage`. `src/api/axios.ts` attaches the access token to every
request and, on a 401, does a single-flight silent refresh before
retrying the original request once.

## Password Policy

8–128 characters, at least one uppercase letter, one lowercase letter,
one number, one special character. Enforced in two places that must stay
in sync:

- Backend: `apps.accounts.validators.PasswordComplexityValidator`, wired
  into `AUTH_PASSWORD_VALIDATORS`.
- Frontend: the same rules as a Zod schema in
  `src/features/auth/schemas/authSchemas.ts`.

Passwords are hashed with **Argon2** (`PASSWORD_HASHERS` puts
`Argon2PasswordHasher` first).

## Forgot / Reset Password

`POST /api/v1/auth/forgot-password/` always returns the same 200
response regardless of whether the identifier matches an account —
prevents account enumeration. If it matches, a `PasswordResetToken`
(30-minute expiry, single-use) is created and an email is queued via
Celery (`send_password_reset_email_task`).

`POST /api/v1/auth/reset-password/` consumes the token — expired or
already-used tokens are rejected with `invalid_token`.

## Roles & Family-Admin Actions

Roles: `family_admin`, `member`, `future_ready`, `read_only`, `auditor`.

A family admin can act on members who share their `family_id` (checked
in `apps.accounts.services.user_management_service`, not by trusting the
client):

- `POST /api/v1/auth/members/<id>/reset-password/` — generates and
  returns a temporary password (share it securely — it is not emailed).
- `POST /api/v1/auth/members/<id>/deactivate/`
- `POST /api/v1/auth/members/<id>/reactivate/`

Cross-family actions are rejected with 403 (`cross_family_action`).

## Audit Trail

Every login, failed login, logout, logout-all, password change/reset,
profile update, avatar update, and family-admin action is written to
`apps.audit.AuditLog` via `apps.audit.services.record()`. Login history
is served from the same table:
`GET /api/v1/auth/login-history/`.

## family_id / household_id — a deliberate placeholder

The User model's `family_id` and `household_id` are plain `UUIDField`s,
not ForeignKeys, because the Family and Household modules don't exist
yet. Once they land, a migration adds the FK constraint — no change to
existing data or to this module's code.
