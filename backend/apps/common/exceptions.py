"""
Custom DRF exception handler.

Wraps every error response (validation, permission, auth, throttling,
uncaught 500s) into the same envelope shape as success_response(), and
logs unexpected exceptions to the security/error log.
"""

import logging

from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.errors")


class ApplicationError(Exception):
    """Base class for domain-level errors raised inside services."""

    def __init__(self, message: str, code: str = "application_error", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def custom_exception_handler(exc, context):
    if isinstance(exc, ApplicationError):
        return Response(
            {"success": False, "message": exc.message, "errors": {"code": exc.code}},
            status=exc.status_code,
        )

    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()

    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception — log with full context, never leak internals to the client.
        logger.exception("Unhandled exception in %s", context.get("view"), exc_info=exc)
        return Response(
            {"success": False, "message": "Internal server error", "errors": {}},
            status=500,
        )

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        errors = detail
    elif isinstance(detail, dict):
        # Field/non-field validation errors, e.g. {"non_field_errors": [...]}
        first_key = next(iter(detail))
        first_value = detail[first_key]
        first_message = (
            first_value[0] if isinstance(first_value, list) and first_value else first_value
        )
        message = str(first_message)
        errors = detail
    else:
        message = "Request failed"
        errors = {"detail": detail}

    response.data = {"success": False, "message": message, "errors": errors}
    return response
