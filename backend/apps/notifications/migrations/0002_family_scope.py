import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    History = apps.get_model("notifications", "LoginHistory")
    Event = apps.get_model("notifications", "SecurityEvent")
    for row in History.objects.filter(family__isnull=True):
        row.family_id = row.member.family_id
        row.save(update_fields=["family"])
    for row in Event.objects.filter(family__isnull=True):
        if row.member_id is None:
            row.delete()
            continue
        row.family_id = row.member.family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial"), ("families", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="loginhistory",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_history",
                to="families.family",
            ),
        ),
        migrations.AddField(
            model_name="securityevent",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="security_events",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="loginhistory",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_history",
                to="families.family",
            ),
        ),
        migrations.AlterField(
            model_name="securityevent",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="security_events",
                to="families.family",
            ),
        ),
    ]
