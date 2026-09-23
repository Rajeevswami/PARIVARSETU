from django.urls import path

from .views import ReferralView

app_name = "referrals"

urlpatterns = [path("", ReferralView.as_view(), name="referral")]
