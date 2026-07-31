import factory

from apps.families.tests.factories import FamilyFactory
from apps.loans.models import Loan
from apps.members.tests.factories import MemberFactory


class LoanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Loan

    family = factory.SubFactory(FamilyFactory)
    borrower = factory.SubFactory(MemberFactory)
    loan_source = "external"
    external_lender_name = "Test Bank"
    title = factory.Faker("sentence", nb_words=3)
    principal_amount = "10000.00"
    interest_type = "none"
    total_amount = "10000.00"
    remaining_amount = "10000.00"
    loan_date = "2026-01-01"
    status = "active"
