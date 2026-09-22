import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    Settlement = apps.get_model("borrow_lend", "Settlement")
    Borrow = apps.get_model("borrow_lend", "BorrowTransaction")
    Lend = apps.get_model("borrow_lend", "LendTransaction")
    Member = apps.get_model("members", "Member")
    for row in Settlement.objects.filter(family__isnull=True):
        parent_model = Borrow if row.reference_type == "borrow" else Lend
        parent = parent_model.objects.filter(id=row.reference_id).first()
        member = Member.objects.filter(id=row.member_id).first()
        family_id = parent.family_id if parent else getattr(member, "family_id", None)
        if family_id is None:
            continue
        row.family_id = family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [
        ("borrow_lend", "0001_initial"),
        ("families", "0001_initial"),
        ("members", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="settlement",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="borrow_lend_settlements",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="settlement",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="borrow_lend_settlements",
                to="families.family",
            ),
        ),
    ]
