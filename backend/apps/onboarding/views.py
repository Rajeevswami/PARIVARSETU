from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response

from .services import onboarding_service


class StepSerializer(serializers.Serializer):
    step = serializers.CharField()


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StepSerializer

    def get(self, request):
        return success_response(data=onboarding_service.get_progress(request.user))

    def post(self, request):
        serializer = StepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = onboarding_service.complete_step(
                user=request.user, step=serializer.validated_data["step"]
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(data=data)
