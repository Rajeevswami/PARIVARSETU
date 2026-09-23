import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    Share = apps.get_model("documents", "DocumentShare")
    Log = apps.get_model("documents", "DocumentAccessLog")
    for row in Share.objects.filter(family__isnull=True):
        row.family_id = row.document.family_id
        row.save(update_fields=["family"])
    for row in Log.objects.filter(family__isnull=True):
        row.family_id = row.document.family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial"), ("families", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="documentshare",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="document_shares",
                to="families.family",
            ),
        ),
        migrations.AddField(
            model_name="documentaccesslog",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="document_access_logs",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="documentshare",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="document_shares",
                to="families.family",
            ),
        ),
        migrations.AlterField(
            model_name="documentaccesslog",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="document_access_logs",
                to="families.family",
            ),
        ),
    ]
