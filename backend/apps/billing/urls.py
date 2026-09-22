from django.urls import path

from .views import BillingWebhookView, CheckoutView, ConfirmCheckoutView, PlanListView

app_name = "billing"

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("checkout/confirm/", ConfirmCheckoutView.as_view(), name="checkout-confirm"),
    path("webhooks/<str:provider>/", BillingWebhookView.as_view(), name="webhook"),
]
