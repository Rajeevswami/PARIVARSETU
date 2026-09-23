"""OpenAPI completeness for the existing /api/v1 surface.

Views stay thin and keep returning ``success_response``. This schema class
and the postprocess hook describe that envelope, JWT bearer auth, tags, and
the file/export responses that are intentionally not JSON.
"""

from __future__ import annotations

import re
from typing import Any

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

TAG_BY_PREFIX = {
    "auth": "Authentication",
    "families": "Families",
    "households": "Households",
    "members": "Members",
    "expenses": "Expenses",
    "loans": "Loans",
    "borrow-lend": "Borrow & Lend",
    "ledger": "Ledger",
    "documents": "Documents",
    "notifications": "Notifications",
    "audit": "Audit",
    "administration": "Administration",
    "billing": "Billing",
    "privacy": "Privacy",
    "referrals": "Referrals",
    "onboarding": "Onboarding",
    "assistant": "Assistant",
    "health": "Operations",
    "metrics": "Operations",
    "dashboard": "Dashboard",
    "reports": "Reports",
}

FILE_PATH_RE = re.compile(r"/(?:export|download)(?:/|$)")
RAW_JWT_PREFIXES = ("/api/v1/auth/token/",)
ERROR_STATUS = {
    "400": "Validation or application error.",
    "401": "Authentication required or token rejected.",
    "403": "Authenticated, but not allowed for this family or role.",
    "404": "Resource not found in the caller's scope.",
    "429": "Rate limit exceeded.",
    "500": "Unexpected server error. Internals are not returned.",
}


def is_file_operation(path: str, view: Any | None = None) -> bool:
    if view is not None and getattr(view, "schema_is_file", False):
        return True
    action = getattr(view, "action", None) if view is not None else None
    if action in {"export", "download"}:
        return True
    return bool(FILE_PATH_RE.search(path or ""))


def is_raw_text_operation(path: str, method: str = "") -> bool:
    """WhatsApp verification must echo hub.challenge as text/plain, not JSON."""

    return method.upper() == "GET" and (path or "").rstrip("/").endswith("/assistant/whatsapp")


def is_raw_jwt_operation(path: str, view: Any | None = None) -> bool:
    if view is not None and view.__class__.__module__.startswith("rest_framework_simplejwt"):
        return True
    return any((path or "").startswith(prefix) for prefix in RAW_JWT_PREFIXES)


def envelope_schema(data_schema: dict[str, Any], *, paginated: bool = False) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "data": data_schema,
    }
    required = ["success", "message", "data"]
    if paginated:
        properties["meta"] = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "current_page": {"type": "integer"},
                "page_size": {"type": "integer"},
                "has_next": {"type": "boolean"},
                "has_previous": {"type": "boolean"},
            },
            "required": [
                "count",
                "total_pages",
                "current_page",
                "page_size",
                "has_next",
                "has_previous",
            ],
        }
        required.append("meta")
    return {"type": "object", "properties": properties, "required": required}


def error_envelope_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "enum": [False]},
            "message": {"type": "string"},
            "errors": {"type": "object", "additionalProperties": True},
        },
        "required": ["success", "message", "errors"],
    }


class FreeformSerializer(serializers.Serializer):
    """Placeholder for endpoints that return JSON without a dedicated serializer."""

    class Meta:
        ref_name = "FreeformObject"

    payload = serializers.JSONField(required=False)


class FamilyNexusAutoSchema(AutoSchema):
    def _can_introspect_serializer(self) -> bool:
        view = self.view
        if getattr(view, "serializer_class", None) is not None:
            return True
        # simplejwt resolves its serializer from this setting path, not serializer_class.
        if getattr(view, "_serializer_class", None):
            return True
        declared = view.__class__.__dict__
        return "get_serializer_class" in declared or "get_serializer" in declared

    def get_tags(self) -> list[str]:
        token = self._tokenize_path()[:1]
        raw = token[0] if token else "api"
        return [TAG_BY_PREFIX.get(raw, raw.replace("-", " ").title())]

    def get_summary(self) -> str | None:
        explicit = super().get_summary()
        if explicit:
            return explicit
        action = getattr(self.view, "action", None) or self.method.lower()
        return f"{str(action).replace('_', ' ').title()} {self.get_tags()[0]}"

    def get_request_serializer(self):
        explicit = getattr(self.view, "request_serializer_class", None)
        if explicit is not None:
            return explicit
        if self._can_introspect_serializer():
            return super().get_request_serializer()
        return FreeformSerializer

    def get_response_serializers(self):
        if is_file_operation(getattr(self, "path", ""), self.view):
            return OpenApiTypes.BINARY
        explicit = getattr(self.view, "response_serializer_class", None)
        if explicit is not None:
            return explicit
        if self._can_introspect_serializer():
            return super().get_response_serializers()
        return FreeformSerializer

    def _get_response_bodies(self, direction: str = "response"):
        if is_raw_text_operation(self.path, self.method):
            return {
                "200": {
                    "description": "Meta webhook verification. Body is the raw hub.challenge.",
                    "content": {"text/plain": {"schema": {"type": "string"}}},
                }
            }
        if is_file_operation(self.path, self.view):
            binary = build_basic_type(OpenApiTypes.BINARY)
            return {
                "200": {
                    "description": "File download. Not wrapped in the JSON envelope.",
                    "content": {
                        "application/octet-stream": {"schema": binary},
                        "text/csv": {"schema": binary},
                        "text/html": {"schema": binary},
                    },
                }
            }
        if self.method == "DELETE" and not is_raw_jwt_operation(self.path, self.view):
            return {
                "200": {
                    "description": "Soft-delete acknowledged with the success envelope.",
                    "content": {
                        "application/json": {
                            "schema": envelope_schema({"type": "object", "nullable": True})
                        }
                    },
                }
            }
        return super()._get_response_bodies(direction)


def _already_enveloped(schema: dict[str, Any] | None, components: dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
        return False
    ref = schema.get("$ref")
    if isinstance(ref, str):
        name = ref.rsplit("/", 1)[-1]
        return _already_enveloped(components.get(name), components)
    properties = schema.get("properties") or {}
    return "success" in properties and "data" in properties


def postprocess_schema(result, generator, request, public):  # noqa: ARG001
    components = result.setdefault("components", {}).setdefault("schemas", {})
    components.setdefault("ErrorEnvelope", error_envelope_schema())
    error_ref = {"$ref": "#/components/schemas/ErrorEnvelope"}

    for path, path_item in result.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            responses = operation.setdefault("responses", {})
            skip_wrap = (
                is_raw_jwt_operation(path)
                or is_file_operation(path)
                or is_raw_text_operation(path, method)
            )
            if not skip_wrap:
                for code, response in responses.items():
                    if not str(code).startswith("2"):
                        continue
                    content = response.get("content", {})
                    json_body = content.get("application/json")
                    if not json_body or _already_enveloped(json_body.get("schema"), components):
                        continue
                    json_body["schema"] = envelope_schema(
                        json_body.get("schema") or {"type": "object"}
                    )
            for code, description in ERROR_STATUS.items():
                responses.setdefault(
                    code,
                    {
                        "description": description,
                        "content": {"application/json": {"schema": error_ref}},
                    },
                )
    return result
