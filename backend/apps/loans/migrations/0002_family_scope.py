import django.db.models.deletion
from django.db import migrations, models


def backfill(apps, schema_editor):
    Installment = apps.get_model("loans", "LoanInstallment")
    Payment = apps.get_model("loans", "LoanPayment")
    for row in Installment.objects.filter(family__isnull=True):
        row.family_id = row.loan.family_id
        row.save(update_fields=["family"])
    for row in Payment.objects.filter(family__isnull=True):
        row.family_id = row.loan.family_id
        row.save(update_fields=["family"])


class Migration(migrations.Migration):
    dependencies = [("loans", "0001_initial"), ("families", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="loaninstallment",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="loan_installments",
                to="families.family",
            ),
        ),
        migrations.AddField(
            model_name="loanpayment",
            name="family",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="loan_payments",
                to="families.family",
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="loaninstallment",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="loan_installments",
                to="families.family",
            ),
        ),
        migrations.AlterField(
            model_name="loanpayment",
            name="family",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="loan_payments",
                to="families.family",
            ),
        ),
    ]
