"""pgvector when the extension is installed; otherwise cosine similarity over JSON."""

import math

from django.db import connection

from apps.assistant.models import Embedding


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def pgvector_status() -> dict:
    """Report the database this process is connected to. Does not invent a Postgres result."""

    vendor = connection.vendor
    status = {
        "vendor": vendor,
        "extension_available": False,
        "extension_installed": False,
        "column_ready": False,
        "json_rows": Embedding.objects.count(),
        "unsynced_rows": None,
    }
    if vendor != "postgresql":
        status["action"] = (
            "This process is not connected to PostgreSQL, so pgvector cannot be enabled here. "
            "JSON embeddings stay in embedding_json and search uses cosine similarity."
        )
        return status
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        status["extension_available"] = cursor.fetchone() is not None
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        status["extension_installed"] = cursor.fetchone() is not None
    status["column_ready"] = vector_column_ready()
    if status["column_ready"]:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM assistant_embedding WHERE embedding IS NULL")
            status["unsynced_rows"] = cursor.fetchone()[0]
        status["action"] = "pgvector column is ready. Run sync_pgvector to copy JSON rows."
    elif status["extension_available"]:
        status["action"] = (
            "Extension is available but the column is missing. Run migrate, then sync_pgvector."
        )
    else:
        status["action"] = (
            "pgvector is not installed on this PostgreSQL image. "
            "Use pgvector/pgvector:pg17, migrate, then sync_pgvector."
        )
    return status


def sync_json_embeddings() -> int:
    """Copy embedding_json into the pgvector column. No-op until that column exists."""

    if not vector_column_ready():
        return 0
    synced = 0
    for row in Embedding.objects.all().iterator():
        if not row.embedding_json:
            continue
        literal = "[" + ",".join(str(float(value)) for value in row.embedding_json) + "]"
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE assistant_embedding SET embedding = %s::vector "
                "WHERE id = %s AND embedding IS NULL",
                [literal, str(row.id)],
            )
            synced += cursor.rowcount
    return synced


def vector_column_ready() -> bool:
    if connection.vendor != "postgresql":
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'assistant_embedding' AND column_name = 'embedding'"
        )
        return cursor.fetchone() is not None


def remember(
    *, family, source_type: str, source_id: str, text: str, embedding: list[float]
) -> Embedding:
    row = Embedding.objects.create(
        family=family,
        source_type=source_type,
        source_id=source_id,
        text=text,
        embedding_json=embedding,
    )
    if vector_column_ready():
        literal = "[" + ",".join(str(float(value)) for value in embedding) + "]"
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE assistant_embedding SET embedding = %s::vector WHERE id = %s",
                [literal, str(row.id)],
            )
    return row


def search(*, family_id, embedding: list[float], limit: int = 5) -> list[dict]:
    if vector_column_ready():
        literal = "[" + ",".join(str(float(value)) for value in embedding) + "]"
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, text, embedding <=> %s::vector AS distance
                FROM assistant_embedding
                WHERE family_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                [literal, str(family_id), literal, limit],
            )
            return [
                {"id": str(row[0]), "text": row[1], "score": 1 - float(row[2])}
                for row in cursor.fetchall()
            ]
    ranked = []
    for row in Embedding.objects.filter(family_id=family_id):
        ranked.append(
            {"id": str(row.id), "text": row.text, "score": cosine(embedding, row.embedding_json)}
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]
