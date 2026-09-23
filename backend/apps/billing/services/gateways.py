"""Payment gateways. Network calls happen only when that provider's keys are set."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings

from apps.common.exceptions import ApplicationError

from ..models import BillingProvider


class GatewayError(ApplicationError):
    def __init__(self, message: str, code: str = "payment_gateway_error"):
        super().__init__(message, code=code, status_code=400)


def sign_stripe(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    stamp = int(time.time()) if timestamp is None else timestamp
    signed = f"{stamp}.".encode() + payload
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={stamp},v1={digest}"


def sign_razorpay(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _verify_stripe(payload: bytes, header: str, secret: str) -> None:
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    stamp = parts.get("t")
    expected = parts.get("v1")
    if not stamp or not expected:
        raise GatewayError("Missing Stripe signature.", code="invalid_signature")
    signed = f"{stamp}.".encode() + payload
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, expected):
        raise GatewayError("Stripe signature did not match.", code="invalid_signature")
    if abs(int(time.time()) - int(stamp)) > 300:
        raise GatewayError("Stripe signature is too old.", code="invalid_signature")


def _post_form(url: str, data: dict, auth: tuple[str, str]) -> dict:
    body = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    token = urllib.request.base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:300]
        raise GatewayError(f"Payment provider rejected the request: {detail}") from exc


class ManualGateway:
    code = BillingProvider.MANUAL

    def create_checkout(self, *, session, success_url: str) -> dict[str, Any]:
        return {
            "provider": self.code,
            "checkout_id": str(session.id),
            "checkout_url": success_url,
        }

    def parse_webhook(self, payload: bytes, headers: dict) -> dict:
        raise GatewayError("Manual billing has no webhook.", code="webhook_not_supported")


class StripeGateway:
    code = BillingProvider.STRIPE

    def create_checkout(self, *, session, success_url: str) -> dict[str, Any]:
        secret = settings.STRIPE_SECRET_KEY
        if not secret:
            raise GatewayError("Stripe is not configured.", code="provider_not_configured")
        price = session.plan.stripe_price_id or settings.STRIPE_PRICE_IDS.get(session.plan.code, "")
        if not price:
            raise GatewayError(
                "Stripe price id is missing for this plan.", code="provider_not_configured"
            )
        remote = _post_form(
            "https://api.stripe.com/v1/checkout/sessions",
            {
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": success_url,
                "line_items[0][price]": price,
                "line_items[0][quantity]": 1,
                "metadata[family_id]": str(session.family_id),
                "metadata[plan_code]": session.plan.code,
                "metadata[checkout_id]": str(session.id),
            },
            (secret, ""),
        )
        session.provider_session_id = remote.get("id", "")
        session.save(update_fields=["provider_session_id"])
        return {
            "provider": self.code,
            "checkout_id": remote.get("id", str(session.id)),
            "checkout_url": remote.get("url", success_url),
        }

    def parse_webhook(self, payload: bytes, headers: dict) -> dict:
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret:
            raise GatewayError(
                "Stripe webhook secret is not configured.", code="provider_not_configured"
            )
        header = headers.get("Stripe-Signature") or headers.get("HTTP_STRIPE_SIGNATURE", "")
        _verify_stripe(payload, header, secret)
        event = json.loads(payload.decode())
        data = event.get("data", {}).get("object", {})
        metadata = data.get("metadata") or {}
        return {
            "event_id": event["id"],
            "event_type": event["type"],
            "family_id": metadata.get("family_id") or data.get("client_reference_id"),
            "plan_code": metadata.get("plan_code"),
            "provider_subscription_id": data.get("subscription") or data.get("id", ""),
            "payload": event,
        }


class RazorpayGateway:
    code = BillingProvider.RAZORPAY

    def create_checkout(self, *, session, success_url: str) -> dict[str, Any]:
        key_id = settings.RAZORPAY_KEY_ID
        secret = settings.RAZORPAY_KEY_SECRET
        if not key_id or not secret:
            raise GatewayError("Razorpay is not configured.", code="provider_not_configured")
        remote = _post_form(
            "https://api.razorpay.com/v1/subscriptions",
            {
                "plan_id": session.plan.razorpay_plan_id,
                "total_count": 12,
                "notes[family_id]": str(session.family_id),
                "notes[plan_code]": session.plan.code,
                "notes[checkout_id]": str(session.id),
            },
            (key_id, secret),
        )
        session.provider_session_id = remote.get("id", "")
        session.save(update_fields=["provider_session_id"])
        return {
            "provider": self.code,
            "checkout_id": remote.get("id", str(session.id)),
            "checkout_url": success_url,
            "key_id": key_id,
        }

    def parse_webhook(self, payload: bytes, headers: dict) -> dict:
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            raise GatewayError(
                "Razorpay webhook secret is not configured.", code="provider_not_configured"
            )
        header = headers.get("X-Razorpay-Signature") or headers.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        expected = sign_razorpay(payload, secret)
        if not hmac.compare_digest(expected, header or ""):
            raise GatewayError("Razorpay signature did not match.", code="invalid_signature")
        event = json.loads(payload.decode())
        entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
        notes = entity.get("notes") or {}
        return {
            "event_id": event.get("id") or entity.get("id"),
            "event_type": event.get("event", ""),
            "family_id": notes.get("family_id"),
            "plan_code": notes.get("plan_code"),
            "provider_subscription_id": entity.get("id", ""),
            "payload": event,
        }


def get_gateway(provider: str):
    if provider == BillingProvider.STRIPE:
        return StripeGateway()
    if provider == BillingProvider.RAZORPAY:
        return RazorpayGateway()
    if provider == BillingProvider.MANUAL:
        return ManualGateway()
    raise GatewayError("Unknown payment provider.", code="unknown_provider")
