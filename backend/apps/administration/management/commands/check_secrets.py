from django.core.management.base import BaseCommand

from apps.common.secrets import missing_secret_names


class Command(BaseCommand):
    help = "Report required secret names that are empty. Values are never printed."

    def handle(self, *args, **options):
        missing = missing_secret_names()
        if not missing:
            self.stdout.write("Required secrets are set.")
            return
        self.stdout.write("Missing: " + ", ".join(missing))
