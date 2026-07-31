import factory

from apps.families.tests.factories import FamilyFactory
from apps.households.models import Household


class HouseholdFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Household

    family = factory.SubFactory(FamilyFactory)
    household_name = factory.Faker("street_name")
