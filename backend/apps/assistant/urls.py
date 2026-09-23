from django.urls import path

from .views import CopilotView, TelegramWebhookView, WhatsAppWebhookView

app_name = "assistant"

urlpatterns = [
    path("copilot/", CopilotView.as_view(), name="copilot"),
    path("telegram/", TelegramWebhookView.as_view(), name="telegram"),
    path("whatsapp/", WhatsAppWebhookView.as_view(), name="whatsapp"),
]
