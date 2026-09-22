"""Rewrite synthetic placeholder addresses left by the old product domain.

Real mailboxes are never touched. The command is idempotent: a second run
finds nothing to change. Collisions are skipped and printed, not overwritten.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.administration.brand_migration import rewrite_placeholder_email
from config.product import LEGACY_PLACEHOLDER_EMAIL_DOMAIN


class Command(BaseCommand):
    help = (
        "Rewrite @placeholder.parivarsetu.app user emails to the FamilyNexus "
        "placeholder domain. Does not rewrite real email addresses."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned changes without writing them.",
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        suffix = f"@{LEGACY_PLACEHOLDER_EMAIL_DOMAIN}"
        planned = []
        skipped = []
        queryset = user_model.objects.filter(email__iendswith=suffix)
        for user in queryset.iterator():
            new_email = rewrite_placeholder_email(
                user.email, new_domain=settings.PLACEHOLDER_EMAIL_DOMAIN
            )
            if new_email is None:
                skipped.append(user.email)
                continue
            collision = user_model.objects.filter(email__iexact=new_email).exclude(pk=user.pk)
            if collision.exists():
                skipped.append(f"{user.email} -> {new_email} (collision)")
                continue
            planned.append((user, new_email))
            self.stdout.write(f"{user.email} -> {new_email}")

        if options["dry_run"]:
            self.stdout.write(f"dry-run: would rewrite {len(planned)}; skipped {len(skipped)}")
            return

        with transaction.atomic():
            for user, new_email in planned:
                user.email = new_email
                user.save(update_fields=["email"])
        self.stdout.write(f"Rewrote {len(planned)} placeholder emails; skipped {len(skipped)}.")
