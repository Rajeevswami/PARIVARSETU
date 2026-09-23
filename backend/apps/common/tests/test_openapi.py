import pytest
from django.urls import get_resolver
from drf_spectacular.generators import EndpointEnumerator, SchemaGenerator

EXCLUDED = ("/api/v1/schema/", "/api/v1/docs/", "/api/v1/redoc/")


def _schema():
    generator = SchemaGenerator()
    return generator, generator.get_schema(request=None, public=True)


def test_every_v1_route_is_documented():
    generator, schema = _schema()
    documented = set(schema["paths"])
    missing = []
    for path, _regex, method, callback in EndpointEnumerator().get_api_endpoints():
        if not path.startswith("/api/v1/") or path in EXCLUDED:
            continue
        view = generator.create_view(callback, method)
        coerced = generator.coerce_path(path, method, view)
        if coerced not in documented:
            missing.append(f"{method} {coerced}")
    assert missing == []
    assert get_resolver().url_patterns


def _resolve(schema, node):
    ref = node.get("$ref") if isinstance(node, dict) else None
    if not ref:
        return node
    return schema["components"]["schemas"][ref.rsplit("/", 1)[-1]]


def test_schema_describes_jwt_tags_and_envelopes():
    _generator, schema = _schema()
    assert schema["info"]["title"] == "FamilyNexus API"
    assert "jwtAuth" in schema["components"]["securitySchemes"]

    families = schema["paths"]["/api/v1/families/"]["get"]
    assert families["tags"] == ["Families"]
    assert {"jwtAuth": []} in families["security"]
    family_schema = _resolve(
        schema, families["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert {"success", "message", "data", "meta"} <= set(family_schema["properties"])

    refresh = schema["paths"]["/api/v1/auth/token/refresh/"]["post"]
    refresh_schema = _resolve(
        schema, refresh["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert "access" in refresh_schema.get("properties", {})
    assert "success" not in refresh_schema.get("properties", {})

    export = schema["paths"]["/api/v1/ledger/journal-register/export/"]["get"]
    assert "text/csv" in export["responses"]["200"]["content"]
    assert "application/json" not in export["responses"]["200"]["content"]


@pytest.mark.django_db
def test_docs_are_public(client):
    schema = client.get("/api/v1/schema/")
    docs = client.get("/api/v1/docs/")
    redoc = client.get("/api/v1/redoc/")
    assert schema.status_code == 200
    assert docs.status_code == 200
    assert redoc.status_code == 200
