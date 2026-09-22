import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    Entry = apps.get_model("ledger", "LedgerEntry")
    Balance = apps.get_model("ledger", "AccountBalance")
    for row in Entry.objects.filter(family__isnull=True):
        row.family_id = row.journal.family_id
        row.save(update_fields=["family"])
    for row in Balance.objects.filter(family__isnull=True):
        row.family_id = row.account.family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [("ledger", "0001_initial"), ("families", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="ledgerentry",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ledger_entries",
                to="families.family",
            ),
        ),
        migrations.AddField(
            model_name="accountbalance",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="account_balances",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="ledgerentry",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ledger_entries",
                to="families.family",
            ),
        ),
        migrations.AlterField(
            model_name="accountbalance",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="account_balances",
                to="families.family",
            ),
        ),
    ]
