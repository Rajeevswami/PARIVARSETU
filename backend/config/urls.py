from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.health import HealthView, MetricsView


class _PublicDocsMixin:
    """Docs must stay reachable. DRF's default permission is IsAuthenticated."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []


class PublicSpectacularAPIView(_PublicDocsMixin, SpectacularAPIView):
    pass


class PublicSpectacularSwaggerView(_PublicDocsMixin, SpectacularSwaggerView):
    pass


class PublicSpectacularRedocView(_PublicDocsMixin, SpectacularRedocView):
    pass


admin.site.site_header = f"{settings.PRODUCT_NAME} administration"
admin.site.site_title = settings.PRODUCT_NAME
admin.site.index_title = "Operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Login is custom (apps.accounts) — it supports email OR mobile,
    # so the stock TokenObtainPairView isn't used. Refresh stays standard.
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/families/", include("apps.families.urls")),
    path("api/v1/households/", include("apps.households.urls")),
    path("api/v1/members/", include("apps.members.urls")),
    path("api/v1/expenses/", include("apps.expenses.urls")),
    path("api/v1/loans/", include("apps.loans.urls")),
    path("api/v1/borrow-lend/", include("apps.borrow_lend.urls")),
    path("api/v1/ledger/", include("apps.ledger.urls")),
    path("api/v1/documents/", include("apps.documents.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/administration/", include("apps.administration.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/privacy/", include("apps.privacy.urls")),
    path("api/v1/referrals/", include("apps.referrals.urls")),
    path("api/v1/onboarding/", include("apps.onboarding.urls")),
    path("api/v1/assistant/", include("apps.assistant.urls")),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/metrics/", MetricsView.as_view(), name="metrics"),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/schema/", PublicSpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", PublicSpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/redoc/", PublicSpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Further feature routers (expenses, loans, ledger, ...) are included
    # here as each module lands.
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
