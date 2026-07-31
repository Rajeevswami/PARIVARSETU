from rest_framework.routers import DefaultRouter
from .views import DocumentCategoryViewSet, DocumentViewSet, StorageView
router=DefaultRouter(); router.register("categories",DocumentCategoryViewSet,basename="document-category"); router.register("storage",StorageView,basename="document-storage"); router.register("",DocumentViewSet,basename="document")
urlpatterns=router.urls
