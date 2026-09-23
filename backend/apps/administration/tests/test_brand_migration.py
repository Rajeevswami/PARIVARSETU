import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.administration.brand_migration import (
    rewrite_database_url,
    rewrite_env_text,
    rewrite_placeholder_email,
)

pytestmark = pytest.mark.django_db


def test_placeholder_rewrite_is_exact_and_idempotent():
    assert (
        rewrite_placeholder_email(
            "9876543210@placeholder.parivarsetu.app",
            new_domain="placeholder.familynexus.app",
        )
        == "9876543210@placeholder.familynexus.app"
    )
    assert (
        rewrite_placeholder_email("ravi@familynexus.app", new_domain="placeholder.familynexus.app")
        is None
    )
    assert (
        rewrite_placeholder_email("ravi@parivarsetu.app", new_domain="placeholder.familynexus.app")
        is None
    )


def test_env_rewrite_leaves_password_and_comments():
    original = "\n".join(
        [
            "# old name parivarsetu",
            "DB_NAME=parivarsetu",
            "DB_USER=parivarsetu",
            "DB_PASSWORD=parivarsetu",
            "DEFAULT_FROM_EMAIL=ParivarSetu <no-reply@parivarsetu.app>",
            "DATABASE_URL=postgresql://parivarsetu:keep-me@db:5432/parivarsetu",
            "",
        ]
    )
    rewritten, notes = rewrite_env_text(original)
    assert "DB_PASSWORD=parivarsetu" in rewritten
    assert "DB_NAME=familynexus" in rewritten
    assert "DB_USER=familynexus" in rewritten
    assert "FamilyNexus <no-reply@familynexus.app>" in rewritten
    assert "postgresql://familynexus:keep-me@db:5432/familynexus" in rewritten
    assert "# old name parivarsetu" in rewritten
    assert any("password unchanged" in note for note in notes)


def test_database_url_without_legacy_identity_is_unchanged():
    url = "postgresql://other:secret@db:5432/other"
    assert rewrite_database_url(url) == url


@pytest.mark.django_db
def test_command_rewrites_only_placeholder_users():
    user_model = get_user_model()
    placeholder = user_model.objects.create_user(
        email="9990001111@placeholder.parivarsetu.app",
        password="Str0ng!Pass1",
        first_name="Guest",
    )
    real = user_model.objects.create_user(
        email="ravi@familynexus.app", password="Str0ng!Pass1", first_name="Ravi"
    )
    call_command("migrate_placeholder_emails")
    placeholder.refresh_from_db()
    real.refresh_from_db()
    assert placeholder.email == "9990001111@placeholder.familynexus.app"
    assert real.email == "ravi@familynexus.app"
    call_command("migrate_placeholder_emails", dry_run=True)
