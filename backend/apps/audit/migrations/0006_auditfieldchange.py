import uuid
import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
 dependencies=[("audit","0005_alter_auditlog_action")]
 operations=[migrations.CreateModel(name="AuditFieldChange",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("field_name",models.CharField(max_length=100)),("old_value",models.JSONField(blank=True,null=True)),("new_value",models.JSONField(blank=True,null=True)),("audit_log",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="field_changes",to="audit.auditlog"))],options={"db_table":"audit_field_change"}),migrations.AddIndex(model_name="auditfieldchange",index=models.Index(fields=["audit_log","field_name"],name="audit_field_audit_l_1ee033_idx"))]
