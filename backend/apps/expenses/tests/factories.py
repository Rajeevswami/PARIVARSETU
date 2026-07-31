import factory

from apps.expenses.models import Expense, ExpenseCategory
from apps.families.tests.factories import FamilyFactory
from apps.members.tests.factories import MemberFactory


class ExpenseCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseCategory
        django_get_or_create = ("family", "name")

    family = factory.SubFactory(FamilyFactory)
    name = factory.Sequence(lambda n: f"Category {n}")


class ExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expense

    family = factory.SubFactory(FamilyFactory)
    title = factory.Faker("sentence", nb_words=3)
    expense_date = "2026-07-01"
    amount = "100.00"
    paid_by = factory.SubFactory(MemberFactory)
    payment_method = "cash"
    visibility = "household"
