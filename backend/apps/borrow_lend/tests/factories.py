import factory

from apps.borrow_lend.models import BorrowTransaction, LendTransaction
from apps.families.tests.factories import FamilyFactory
from apps.members.tests.factories import MemberFactory


class BorrowTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BorrowTransaction

    family = factory.SubFactory(FamilyFactory)
    borrower = factory.SubFactory(MemberFactory)
    external_lender_name = "Test Lender"
    amount = "1000.00"
    date = "2026-01-01"
    payment_method = "cash"


class LendTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LendTransaction

    family = factory.SubFactory(FamilyFactory)
    giver = factory.SubFactory(MemberFactory)
    external_receiver_name = "Test Receiver"
    amount = "1000.00"
    date = "2026-01-01"
    payment_method = "cash"
