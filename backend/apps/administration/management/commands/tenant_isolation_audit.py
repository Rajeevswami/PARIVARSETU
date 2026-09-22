from django.core.management.base import BaseCommand

from apps.common.tenant_audit import models_missing_family_scope


class Command(BaseCommand):
    help = "List tenant models that are not scoped by family and are not a known child row."

    def handle(self, *args, **options):
        missing = models_missing_family_scope()
        if not missing:
            self.stdout.write("No unscoped tenant models.")
            return
        for label in missing:
            self.stdout.write(label)
