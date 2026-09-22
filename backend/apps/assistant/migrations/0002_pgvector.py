from django.db import migrations


def enable_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        if cursor.fetchone() is None:
            return
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(
            "ALTER TABLE assistant_embedding ADD COLUMN IF NOT EXISTS embedding vector(1536)"
        )


class Migration(migrations.Migration):
    dependencies = [("assistant", "0001_initial")]
    operations = [migrations.RunPython(enable_pgvector, migrations.RunPython.noop)]
