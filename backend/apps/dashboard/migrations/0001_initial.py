# Generated manually because the local Python runtime lacks project dependencies.
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [("families", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
      migrations.CreateModel(name="DashboardPreference", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("dashboard_type", models.CharField(default="family", max_length=20)), ("layout", models.JSONField(blank=True, default=dict)), ("default_date_range", models.CharField(default="current_month", max_length=30)), ("updated_at", models.DateTimeField(auto_now=True)), ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="dashboard_preference", to=settings.AUTH_USER_MODEL))], options={"db_table":"dashboard_preference"}),
      migrations.CreateModel(name="AnalyticsCache", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("cache_key", models.CharField(max_length=255)), ("payload", models.JSONField(default=dict)), ("expires_at", models.DateTimeField()), ("created_at", models.DateTimeField(auto_now_add=True)), ("family", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analytics_caches", to="families.family"))], options={"db_table":"dashboard_analytics_cache"}),
      migrations.AddConstraint(model_name="analyticscache", constraint=models.UniqueConstraint(fields=("family","cache_key"), name="dashboard_cache_key_per_family")),
      migrations.AddIndex(model_name="analyticscache", index=models.Index(fields=["family","expires_at"], name="dashboard_a_family__d903fb_idx")),
    ]
