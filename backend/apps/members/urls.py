from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AcceptInvitationView, InvitationViewSet, MemberViewSet, RejectInvitationView

app_name = "members"

router = DefaultRouter()
router.register("invitations", InvitationViewSet, basename="invitation")
router.register("", MemberViewSet, basename="member")

urlpatterns = [
    path("invitations/accept/", AcceptInvitationView.as_view(), name="accept_invitation"),
    path("invitations/reject/", RejectInvitationView.as_view(), name="reject_invitation"),
] + router.urls
