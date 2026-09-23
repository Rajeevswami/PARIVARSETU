from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .serializers import CheckoutSerializer, ConfirmCheckoutSerializer
from .services import entitlements, subscription_service
from .services.gateways import GatewayError, get_gateway


class PlanListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def get(self, request):
        plans = [
            {
                "code": plan.code,
                "name": plan.name,
                "price_inr_paise": plan.price_inr_paise,
                "price_usd_cents": plan.price_usd_cents,
                "member_limit": plan.member_limit,
                "household_limit": plan.household_limit,
                "monthly_expense_limit": plan.monthly_expense_limit,
                "storage_mb": plan.storage_mb,
                "ai_enabled": plan.ai_enabled,
            }
            for plan in subscription_service.list_plans()
        ]
        current = entitlements.current_subscription(request.user.family)
        return success_response(
            data={
                "plans": plans,
                "current": (
                    None
                    if current is None
                    else {
                        "code": current.plan.code,
                        "status": current.status,
                        "provider": current.provider,
                    }
                ),
            }
        )


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.family_id is None:
            return error_response("Create a family before choosing a plan.", status_code=400)
        success_url = (
            serializer.validated_data.get("success_url") or f"{settings.FRONTEND_URL}/billing"
        )
        try:
            data = subscription_service.start_checkout(
                actor=request.user,
                family=request.user.family,
                plan_code=serializer.validated_data["plan_code"],
                provider=serializer.validated_data["provider"],
                success_url=success_url,
            )
        except (ApplicationError, GatewayError) as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(data=data, message="Checkout started", status_code=201)


class ConfirmCheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConfirmCheckoutSerializer

    def post(self, request):
        serializer = ConfirmCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = subscription_service.confirm_manual(
                actor=request.user,
                family=request.user.family,
                checkout_id=str(serializer.validated_data["checkout_id"]),
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(
            data={"plan": subscription.plan.code, "status": subscription.status}
        )


class BillingWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request, provider):
        try:
            event = get_gateway(provider).parse_webhook(request.body, request.headers)
            event["provider"] = provider
            result = subscription_service.apply_event(event)
        except (ApplicationError, GatewayError, KeyError, ValueError) as exc:
            message = getattr(exc, "message", "Invalid webhook.")
            code = getattr(exc, "code", "invalid_event")
            return error_response(message, {"code": code}, 400)
        return success_response(data=result)
