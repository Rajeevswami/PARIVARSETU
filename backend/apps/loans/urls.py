from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InterestConfigurationView, LoanTypeViewSet, LoanViewSet, ReminderViewSet

app_name = "loans"

router = DefaultRouter()
router.register("types", LoanTypeViewSet, basename="loan-type")
router.register("reminders", ReminderViewSet, basename="loan-reminder")
router.register("", LoanViewSet, basename="loan")

urlpatterns = [
    path(
        "interest-configurations/",
        InterestConfigurationView.as_view(),
        name="interest_configurations",
    ),
] + router.urls
