from django.urls import path
from rest_framework.routers import DefaultRouter

from .ops_views import OpsDashboardView
from .views import (
    BackupView,
    ConfigurationView,
    FinancialYearView,
    FlagsView,
    LookupView,
    RestoreView,
    SettingsView,
)

r = DefaultRouter()
r.register("settings", SettingsView, basename="system-setting")
r.register("features", FlagsView, basename="feature-flag")
r.register("configuration", ConfigurationView, basename="configuration")
r.register("lookups", LookupView, basename="lookup")
r.register("financial-years", FinancialYearView, basename="financial-year")
r.register("backups", BackupView, basename="backup")
r.register("restores", RestoreView, basename="restore")
urlpatterns = [path("ops/", OpsDashboardView.as_view(), name="ops-dashboard")] + r.urls
