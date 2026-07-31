from django.urls import path
from .views import ExportHistoryView, ExportView, ReportDataView, SavedReportsView, SchedulesView
urlpatterns = [path("saved/", SavedReportsView.as_view()), path("schedules/", SchedulesView.as_view()), path("exports/", ExportHistoryView.as_view()), path("<str:report_type>/export/<str:export_format>/", ExportView.as_view()), path("<str:report_type>/", ReportDataView.as_view())]

