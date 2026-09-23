from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.response import success_response


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        database = "ok"
        cache_status = "ok"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            database = "error"
        try:
            cache.set("health", "1", 5)
        except Exception:
            cache_status = "error"
        status_code = 200 if database == "ok" else 503
        return success_response(
            data={
                "status": "ok" if status_code == 200 else "degraded",
                "database": database,
                "cache": cache_status,
            },
            status_code=status_code,
        )


class MetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            from apps.common.response import error_response

            return error_response("Staff access required.", status_code=403)
        from django.contrib.auth import get_user_model

        from apps.families.models import Family

        return success_response(
            data={
                "families": Family.objects.filter(is_deleted=False).count(),
                "users": get_user_model().objects.filter(is_deleted=False).count(),
            }
        )
