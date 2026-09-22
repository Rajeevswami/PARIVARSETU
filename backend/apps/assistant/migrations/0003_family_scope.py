import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill(apps, schema_editor):
    Message = apps.get_model("assistant", "Message")
    for row in Message.objects.filter(family__isnull=True):
        row.family_id = row.conversation.family_id
        row.save(update_fields=["family"])
    ChannelLink = apps.get_model("assistant", "ChannelLink")
    User = apps.get_model("accounts", "User")
    for row in ChannelLink.objects.filter(family__isnull=True):
        user = User.objects.filter(id=row.user_id).first()
        if user is None or user.family_id is None:
            row.delete()
            continue
        row.family_id = user.family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0002_pgvector"),
        ("families", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name="message",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assistant_messages",
                to="families.family",
            ),
        ),
        migrations.AddField(
            model_name="channellink",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="channel_links",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="message",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assistant_messages",
                to="families.family",
            ),
        ),
        migrations.AlterField(
            model_name="channellink",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="channel_links",
                to="families.family",
            ),
        ),
    ]
