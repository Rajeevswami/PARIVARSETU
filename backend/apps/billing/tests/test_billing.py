import json
import time

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.billing.models import PaymentEvent, PlanCode, Subscription
from apps.billing.services.gateways import sign_razorpay, sign_stripe
from apps.billing.services.subscription_service import attach_free
from apps.common.exceptions import ApplicationError
from apps.expenses.tests.factories import ExpenseFactory
from apps.families.tests.factories import FamilyFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    response = client.post(
        reverse("accounts:login"),
        {"identifier": user.email, "password": "Str0ng!Pass1"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['tokens']['access']}")
    return client


class TestPlansAndCheckout:
    def test_manual_checkout_activates_family_plan(self):
        family = FamilyFactory()
        admin = UserFactory(family=family, role="family_admin")
        client = _client(admin)

        started = client.post(
            reverse("billing:checkout"),
            {"plan_code": "family", "provider": "manual"},
            format="json",
        )
        assert started.status_code == 201
        confirmed = client.post(
            reverse("billing:checkout-confirm"),
            {"checkout_id": started.data["data"]["checkout_id"]},
            format="json",
        )
        assert confirmed.status_code == 200
        family.refresh_from_db()
        assert family.subscription_plan == "basic"
        assert Subscription.objects.get(family=family).plan.code == PlanCode.FAMILY

    def test_member_cannot_start_checkout(self):
        family = FamilyFactory()
        member = UserFactory(family=family, role="member")
        response = _client(member).post(
            reverse("billing:checkout"),
            {"plan_code": "premium", "provider": "manual"},
            format="json",
        )
        assert response.status_code == 403

    def test_free_plan_blocks_the_51st_expense(self):
        from apps.billing.services.entitlements import assert_can_add

        family = FamilyFactory()
        member = MemberFactory(family=family, user=UserFactory(family=family))
        attach_free(family)
        plan = Subscription.objects.get(family=family).plan
        plan.monthly_expense_limit = 1
        plan.save()
        ExpenseFactory(family=family, paid_by=member)
        with pytest.raises(ApplicationError) as caught:
            assert_can_add(family, "expenses")
        assert caught.value.code == "plan_limit_exceeded"

    def test_family_without_subscription_stays_unlimited(self):
        from apps.billing.services.entitlements import assert_can_add

        assert_can_add(FamilyFactory(), "expenses") is None


class TestWebhooks:
    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test")
    def test_signed_stripe_event_changes_plan(self):
        family = FamilyFactory()
        attach_free(family)
        payload = json.dumps(
            {
                "id": "evt_stripe_1",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "metadata": {"family_id": str(family.id), "plan_code": "premium"},
                        "subscription": "sub_1",
                    }
                },
            }
        ).encode()
        signature = sign_stripe(payload, "whsec_test", timestamp=int(time.time()))
        response = APIClient().post(
            reverse("billing:webhook", args=["stripe"]),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )
        assert response.status_code == 200
        assert Subscription.objects.get(family=family).plan.code == PlanCode.PREMIUM
        again = APIClient().post(
            reverse("billing:webhook", args=["stripe"]),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )
        assert again.data["data"]["status"] == "duplicate"
        assert PaymentEvent.objects.filter(event_id="evt_stripe_1").count() == 1

    def test_unsigned_webhook_is_rejected_when_secret_missing(self):
        response = APIClient().post(
            reverse("billing:webhook", args=["stripe"]),
            data=b"{}",
            content_type="application/json",
        )
        assert response.status_code == 400

    @override_settings(RAZORPAY_WEBHOOK_SECRET="rzp_test")
    def test_razorpay_signature(self):
        family = FamilyFactory()
        attach_free(family)
        payload = json.dumps(
            {
                "id": "evt_rzp_1",
                "event": "subscription.activated",
                "payload": {
                    "subscription": {
                        "entity": {
                            "id": "sub_rzp",
                            "notes": {"family_id": str(family.id), "plan_code": "family"},
                        }
                    }
                },
            }
        ).encode()
        signature = sign_razorpay(payload, "rzp_test")
        response = APIClient().post(
            reverse("billing:webhook", args=["razorpay"]),
            data=payload,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=signature,
        )
        assert response.status_code == 200
        assert Subscription.objects.get(family=family).plan.code == PlanCode.FAMILY
