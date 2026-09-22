from pathlib import Path

from django.core.management.base import BaseCommand

from apps.administration.services.backup_service import export_family
from apps.families.models import Family


class Command(BaseCommand):
    help = "Write one JSON file per active family. Use volume snapshots for full disaster recovery."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="/tmp/familynexus-backups")

    def handle(self, *args, **options):
        destination = Path(options["output"])
        count = 0
        for family in Family.objects.filter(is_deleted=False):
            export_family(family, destination)
            count += 1
        self.stdout.write(f"Exported {count} families to {destination}")
