import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from ai_services.analytics import anomalies, forecast_next_month, suggest_category
from ai_services.bots import parse_expense_command, verify_whatsapp
from ai_services.copilot import answer
from ai_services.vectors import cosine
from apps.accounts.tests.factories import UserFactory
from apps.assistant.models import ChannelLink
from apps.billing.models import PlanCode
from apps.billing.services.subscription_service import attach_free
from apps.families.tests.factories import FamilyFactory

pytestmark = pytest.mark.django_db


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)

    def complete(self, *, system, messages, tools):
        return self.responses.pop(0)


class FakeExpense:
    def __init__(self, amount, month):
        self.amount = Decimal(amount)
        self.expense_date = month
        self.id = "x"
        self.title = "School fees"


def test_forecast_and_category_are_deterministic():
    from datetime import date

    expenses = [FakeExpense("100", date(2026, 7, 1)), FakeExpense("300", date(2026, 8, 1))]
    assert forecast_next_month(expenses)["next_month"] == "200.00"
    assert suggest_category("School bus", ["Education", "Medical"]) == "Education"
    assert anomalies(expenses) == []


def test_sync_is_a_noop_until_the_vector_column_exists():
    from django.db import connection

    from ai_services.vectors import pgvector_status, sync_json_embeddings

    status = pgvector_status()
    assert status["vendor"] == connection.vendor
    if status["column_ready"]:
        assert status["extension_available"] is True
        return
    assert status["column_ready"] is False
    assert sync_json_embeddings() == 0


def test_cosine_ranks_identical_vectors_first():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0)


def test_copilot_runs_a_tool_then_answers():
    family = FamilyFactory()
    user = UserFactory(family=family)
    attach_free(family)
    subscription = family.billing_subscription
    subscription.plan = subscription.plan.__class__.objects.get(code=PlanCode.PREMIUM)
    subscription.status = "active"
    subscription.save()
    transport = ScriptedTransport(
        [
            {
                "content": [
                    {"type": "tool_use", "id": "tool_1", "name": "ledger_summary", "input": {}}
                ]
            },
            {"content": [{"type": "text", "text": "No expenses yet."}]},
        ]
    )
    result = answer(
        user=user, family_id=family.id, text="summarise", language="en", transport=transport
    )
    assert result["tools"] == ["ledger_summary"]
    assert result["message"] == "No expenses yet."


def test_free_plan_cannot_use_the_copilot():
    family = FamilyFactory()
    user = UserFactory(family=family)
    attach_free(family)
    from apps.common.exceptions import ApplicationError

    with pytest.raises(ApplicationError):
        answer(user=user, family_id=family.id, text="hello", transport=ScriptedTransport([]))


@override_settings(WHATSAPP_VERIFY_TOKEN="verify-me")
def test_whatsapp_verification_returns_the_raw_challenge():
    response = APIClient().get(
        reverse("assistant:whatsapp"),
        {
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "1158201444",
        },
    )
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response.content == b"1158201444"
    assert b"success" not in response.content


@override_settings(WHATSAPP_VERIFY_TOKEN="")
def test_whatsapp_verification_rejects_an_empty_configured_token():
    response = APIClient().get(
        reverse("assistant:whatsapp"),
        {"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "1158201444"},
    )
    assert response.status_code == 403


@override_settings(WHATSAPP_APP_SECRET="wa_secret", TELEGRAM_WEBHOOK_SECRET="tg_secret")
def test_channel_expense_command():
    assert parse_expense_command("kharcha chai 50")["title"] == "chai"
    family = FamilyFactory()
    user = UserFactory(family=family)
    from apps.members.tests.factories import MemberFactory

    MemberFactory(family=family, user=user)
    ChannelLink.objects.create(user=user, channel="telegram", address="99")
    body = hmac.new(b"wa_secret", b"{}", hashlib.sha256).hexdigest()
    assert verify_whatsapp(b"{}", f"sha256={body}")
    response = APIClient().post(
        reverse("assistant:telegram"),
        data=json.dumps({"message": {"chat": {"id": 99}, "text": "expense milk 40"}}),
        content_type="application/json",
        HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="tg_secret",
    )
    assert response.status_code == 200
    assert "expense_id" in response.data["data"]
