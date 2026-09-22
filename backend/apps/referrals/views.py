from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .services import referral_service


class RedeemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=16)


class ReferralView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RedeemSerializer

    def get(self, request):
        code = referral_service.get_or_create_code(request.user)
        return success_response(
            data={"code": code.code, "uses": code.redemptions.count(), "max_uses": code.max_uses}
        )

    def post(self, request):
        serializer = RedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            redemption = referral_service.redeem(
                user=request.user, code_value=serializer.validated_data["code"]
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(
            data={"credit_days": redemption.credit_days}, message="Referral applied"
        )
