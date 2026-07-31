from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AttachmentDownloadView, ExpenseCategoryViewSet, ExpenseViewSet

app_name = "expenses"

router = DefaultRouter()
router.register("categories", ExpenseCategoryViewSet, basename="expense-category")
router.register("", ExpenseViewSet, basename="expense")

urlpatterns = [
    path(
        "attachments/<uuid:attachment_id>/",
        AttachmentDownloadView.as_view(),
        name="attachment_download",
    ),
] + router.urls
