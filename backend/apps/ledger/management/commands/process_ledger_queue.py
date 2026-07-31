from django.core.management.base import BaseCommand

from apps.ledger.services.queue_consumer import process_pending_postings


class Command(BaseCommand):
    help = "Drains apps.expenses and apps.loans LedgerPostingQueue rows into posted Journals."

    def handle(self, *args, **options):
        result = process_pending_postings()
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {result['processed']} posting(s), {result['failed']} failed."
            )
        )
