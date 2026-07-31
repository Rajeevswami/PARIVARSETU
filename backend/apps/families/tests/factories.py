import factory

from apps.families.models import Family


class FamilyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Family

    family_name = factory.Faker("last_name")
    country = "India"
    city = "Jaipur"
