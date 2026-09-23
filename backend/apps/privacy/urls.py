from django.urls import path

from .views import AcceptanceView, ConsentView, DeletionView, ExportView, LegalDocumentView

app_name = "privacy"

urlpatterns = [
    path("legal/<str:document>/", LegalDocumentView.as_view(), name="legal"),
    path("consent/", ConsentView.as_view(), name="consent"),
    path("accept/", AcceptanceView.as_view(), name="accept"),
    path("data-export/", ExportView.as_view(), name="export"),
    path("deletion/", DeletionView.as_view(), name="deletion"),
]
