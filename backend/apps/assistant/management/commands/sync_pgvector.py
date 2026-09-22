from django.core.management.base import BaseCommand

from ai_services.vectors import pgvector_status, sync_json_embeddings


class Command(BaseCommand):
    help = "Report pgvector status and copy JSON embeddings into the vector column when it exists."

    def handle(self, *args, **options):
        status = pgvector_status()
        synced = sync_json_embeddings()
        self.stdout.write(f"vendor: {status['vendor']}")
        self.stdout.write(f"extension_available: {str(status['extension_available']).lower()}")
        self.stdout.write(f"extension_installed: {str(status['extension_installed']).lower()}")
        self.stdout.write(f"column_ready: {str(status['column_ready']).lower()}")
        self.stdout.write(f"json_rows: {status['json_rows']}")
        self.stdout.write(f"unsynced_rows: {status['unsynced_rows']}")
        self.stdout.write(f"synced: {synced}")
        self.stdout.write(status["action"])
