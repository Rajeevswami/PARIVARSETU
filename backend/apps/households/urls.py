from rest_framework.routers import DefaultRouter

from .views import HouseholdViewSet

app_name = "households"

router = DefaultRouter()
router.register("", HouseholdViewSet, basename="household")

urlpatterns = router.urls
