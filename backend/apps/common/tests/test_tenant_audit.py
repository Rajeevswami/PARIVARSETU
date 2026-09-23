import pytest
from django.core.exceptions import ValidationError

from apps.accounts.tests.factories import UserFactory
from apps.assistant.models import ChannelLink, Conversation, Message
from apps.billing.models import Plan
from apps.common.tenant_audit import PLATFORM_MODELS, models_missing_family_scope
from apps.families.tests.factories import FamilyFactory
from apps.members.tests.factories import MemberFactory

pytestmark = pytest.mark.django_db


def test_tenant_isolation_audit_is_clean():
    assert models_missing_family_scope() == []
    assert "billing.Plan" in PLATFORM_MODELS
    assert not any(field.name == "family" for field in Plan._meta.fields)


def test_child_rows_are_stamped_with_the_parent_family():
    family = FamilyFactory()
    user = UserFactory(family=family)
    conversation = Conversation.objects.create(family=family, user=user, title="scope")
    message = Message.objects.create(conversation=conversation, role="user", content="hello")
    link = ChannelLink.objects.create(user=user, channel="telegram", address="scope-1")
    assert message.family_id == family.id
    assert link.family_id == family.id


def test_channel_link_rejects_a_user_without_a_family():
    user = UserFactory()
    with pytest.raises(ValidationError):
        ChannelLink.objects.create(user=user, channel="telegram", address="no-family")


def test_settlement_rejects_a_member_from_another_family():
    from datetime import date
    from decimal import Decimal

    from apps.borrow_lend.models import BorrowTransaction, Settlement

    family = FamilyFactory()
    other = FamilyFactory()
    borrower = MemberFactory(family=family, user=UserFactory(family=family))
    outsider = MemberFactory(family=other, user=UserFactory(family=other))
    transaction = BorrowTransaction.objects.create(
        family=family,
        borrower=borrower,
        amount=Decimal("100.00"),
        date=date.today(),
    )
    with pytest.raises(ValidationError):
        Settlement.objects.create(
            reference_type="borrow",
            reference_id=transaction.id,
            member=outsider,
            amount=Decimal("10.00"),
            settled_amount=Decimal("10.00"),
            remaining_amount=Decimal("90.00"),
            settlement_date=date.today(),
        )
