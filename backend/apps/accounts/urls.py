from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("logout-all/", views.LogoutAllView.as_view(), name="logout_all"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset_password"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/avatar/", views.AvatarUploadView.as_view(), name="profile_avatar"),
    path("login-history/", views.LoginHistoryView.as_view(), name="login_history"),
    path(
        "members/<uuid:member_id>/reset-password/",
        views.MemberResetPasswordView.as_view(),
        name="member_reset_password",
    ),
    path(
        "members/<uuid:member_id>/deactivate/",
        views.MemberDeactivateView.as_view(),
        name="member_deactivate",
    ),
    path(
        "members/<uuid:member_id>/reactivate/",
        views.MemberReactivateView.as_view(),
        name="member_reactivate",
    ),
]
