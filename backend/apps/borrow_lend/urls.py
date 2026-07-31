from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BorrowTransactionViewSet, LendTransactionViewSet, SettlementView

app_name = "borrow_lend"

router = DefaultRouter()
router.register("borrow", BorrowTransactionViewSet, basename="borrow")
router.register("lend", LendTransactionViewSet, basename="lend")

urlpatterns = [
    path("settlements/", SettlementView.as_view(), name="settlement"),
] + router.urls
