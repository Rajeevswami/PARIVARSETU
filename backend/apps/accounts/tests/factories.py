import factory

from apps.accounts.models import User, UserRole, UserStatus


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@parivarsetu.app")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.MEMBER
    status = UserStatus.ACTIVE
    is_verified = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "Str0ng!Pass1")
        if create:
            self.save()
