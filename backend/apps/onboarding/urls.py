from django.urls import path

from .views import OnboardingView

app_name = "onboarding"

urlpatterns = [path("", OnboardingView.as_view(), name="progress")]
