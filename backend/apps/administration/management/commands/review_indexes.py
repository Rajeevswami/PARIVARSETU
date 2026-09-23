from django.core.management.base import BaseCommand

from apps.common.index_review import family_indexes_missing


class Command(BaseCommand):
    help = "List family-scoped models whose indexes do not start with family."

    def handle(self, *args, **options):
        missing = family_indexes_missing()
        if not missing:
            self.stdout.write("Family indexes look complete.")
            return
        for label in missing:
            self.stdout.write(label)
