from django.urls import path
from .views import AnalyticsView, DashboardView, PreferenceView
urlpatterns = [path("", DashboardView.as_view()), path("analytics/", AnalyticsView.as_view()), path("preferences/", PreferenceView.as_view())]
