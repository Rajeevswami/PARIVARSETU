"""
Standardized API response envelope used across all endpoints.

Every API response follows the same shape so frontend consumption is
predictable regardless of which endpoint is called.
"""

from typing import Any, Optional

from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    meta: Optional[dict] = None,
) -> Response:
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def error_response(
    message: str = "An error occurred",
    errors: Optional[dict] = None,
    status_code: int = 400,
) -> Response:
    payload = {
        "success": False,
        "message": message,
        "errors": errors or {},
    }
    return Response(payload, status=status_code)
