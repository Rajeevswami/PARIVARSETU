from rest_framework.routers import DefaultRouter

from .views import FamilyViewSet

app_name = "families"

router = DefaultRouter()
router.register("", FamilyViewSet, basename="family")

urlpatterns = router.urls
