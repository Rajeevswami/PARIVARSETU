from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from apps.billing.models import PaymentEvent, Subscription
from apps.common.response import success_response
from apps.families.models import Family
from apps.privacy.models import DeletionRequest


class OpsDashboardView(APIView):
    """Platform operations. Family admins do not see other tenants here."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        return success_response(
            data={
                "families": Family.objects.filter(is_deleted=False).count(),
                "users": get_user_model().objects.filter(is_deleted=False).count(),
                "subscriptions": list(
                    Subscription.objects.values("status").annotate(count=Count("id"))
                ),
                "failed_payments": PaymentEvent.objects.filter(status="failed").count(),
                "deletion_requests": DeletionRequest.objects.count(),
            }
        )
