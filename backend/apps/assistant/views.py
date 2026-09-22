import hmac

from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ai_services.bots import record_channel_expense, verify_telegram, verify_whatsapp
from ai_services.copilot import answer
from apps.assistant.models import ChannelLink
from apps.common.exceptions import ApplicationError
from apps.common.response import error_response, success_response


class CopilotSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    language = serializers.ChoiceField(choices=["en", "hi"], default="en")


class CopilotView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CopilotSerializer

    def post(self, request):
        serializer = CopilotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = answer(
                user=request.user,
                family_id=request.user.family_id,
                text=serializer.validated_data["message"],
                language=serializer.validated_data["language"],
            )
        except ApplicationError as exc:
            return error_response(exc.message, {"code": exc.code}, exc.status_code)
        return success_response(data=data)


class TelegramWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        if not verify_telegram(request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")):
            return error_response("Invalid Telegram secret.", status_code=403)
        message = request.data.get("message") or {}
        chat = str((message.get("chat") or {}).get("id", ""))
        text = message.get("text") or ""
        link = (
            ChannelLink.objects.filter(channel="telegram", address=chat)
            .select_related("user")
            .first()
        )
        if link is None or link.family_id != link.user.family_id:
            return success_response(data={"ignored": True})
        try:
            expense = record_channel_expense(user=link.user, text=text)
        except ApplicationError as exc:
            return success_response(data={"error": exc.code})
        return success_response(data={"expense_id": str(expense.id)})


class WhatsAppWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        from django.conf import settings

        configured = settings.WHATSAPP_VERIFY_TOKEN
        supplied = request.query_params.get("hub.verify_token") or ""
        mode = request.query_params.get("hub.mode")
        challenge = request.query_params.get("hub.challenge")
        token_matches = bool(configured) and hmac.compare_digest(supplied, configured)
        if mode != "subscribe" or not token_matches or challenge is None:
            return error_response("Invalid verify token.", status_code=403)
        return HttpResponse(challenge, content_type="text/plain", status=200)

    def post(self, request):
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_whatsapp(request.body, signature):
            return error_response("Invalid WhatsApp signature.", status_code=403)
        return success_response(data={"accepted": True})
