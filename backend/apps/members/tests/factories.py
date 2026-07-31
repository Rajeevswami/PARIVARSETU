import factory

from apps.accounts.tests.factories import UserFactory
from apps.families.tests.factories import FamilyFactory
from apps.members.models import Member


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Member

    family = factory.SubFactory(FamilyFactory)
    user = factory.SubFactory(UserFactory)
    display_name = factory.Faker("first_name")
