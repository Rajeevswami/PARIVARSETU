import csv
from django.http import HttpResponse
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.common.response import success_response
from apps.common.permissions import IsFamilyAdmin
from apps.audit.services.audit_service import record
from apps.expenses.models import Expense
from apps.loans.models import Loan
from apps.borrow_lend.models import BorrowTransaction, LendTransaction, Settlement
from .models import SavedReport, ReportSchedule, ReportExportHistory

REPORTS = {"expense": (Expense, ("expense_number","title","expense_date","amount","payment_method","status")), "loan": (Loan, ("loan_number","title","loan_date","principal_amount","remaining_amount","status")), "borrow": (BorrowTransaction, ("transaction_number","date","amount","status")), "lend": (LendTransaction, ("transaction_number","date","amount","status")), "settlement": (Settlement, ("settlement_date","amount","remaining_amount","status"))}
def report_rows(request, report_type):
    model, fields = REPORTS.get(report_type, REPORTS["expense"])
    qs = model.objects.filter(family_id=request.user.family_id, is_deleted=False) if hasattr(model, "family") else model.objects.filter(member__family_id=request.user.family_id)
    for key in ("status", "household", "payment_method", "category"):
        if request.query_params.get(key): qs = qs.filter(**{key: request.query_params[key]})
    date_field = "expense_date" if report_type == "expense" else "loan_date" if report_type == "loan" else "date" if report_type in ("borrow", "lend") else "settlement_date"
    if request.query_params.get("date_from"): qs = qs.filter(**{f"{date_field}__gte": request.query_params["date_from"]})
    if request.query_params.get("date_to"): qs = qs.filter(**{f"{date_field}__lte": request.query_params["date_to"]})
    return fields, qs.order_by(f"-{date_field}")

class ReportDataView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, report_type):
        fields, qs = report_rows(request, report_type)
        rows = list(qs.values(*fields)[:1000]); record(actor=request.user, action="report_generated", family_id=request.user.family_id, metadata={"report_type": report_type})
        return success_response(data={"report_type": report_type, "columns": fields, "rows": rows, "count": len(rows)})

class ExportView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, report_type, export_format):
        if export_format not in ("csv", "excel", "print"): return success_response(data=None, message="Supported exports are CSV, Excel and print", status_code=400)
        fields, qs = report_rows(request, report_type); rows = list(qs.values(*fields)[:10000])
        ReportExportHistory.objects.create(family_id=request.user.family_id, user=request.user, report_type=report_type, export_format=export_format, filters=dict(request.query_params), row_count=len(rows))
        record(actor=request.user, action="report_exported", family_id=request.user.family_id, metadata={"report_type": report_type, "format": export_format})
        response = HttpResponse(content_type="text/csv" if export_format != "print" else "text/html")
        response["Content-Disposition"] = f'attachment; filename="{report_type}-report.{"html" if export_format == "print" else "csv"}"'
        if export_format == "print": response.write("<table><thead><tr>" + "".join(f"<th>{f}</th>" for f in fields) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{row.get(f, '')}</td>" for f in fields) + "</tr>" for row in rows) + "</tbody></table>")
        else:
            writer = csv.DictWriter(response, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        return response

class SavedReportsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        reports = SavedReport.objects.filter(family_id=request.user.family_id).filter(Q(owner=request.user)|Q(is_shared=True)).values()
        return success_response(data=list(reports))
    def post(self, request):
        report = SavedReport.objects.create(family_id=request.user.family_id, owner=request.user, name=request.data["name"], report_type=request.data["report_type"], filters=request.data.get("filters", {}), is_shared=request.data.get("is_shared", False))
        return success_response(data={"id": str(report.id)}, message="Report saved", status_code=201)

class SchedulesView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]
    def get(self, request): return success_response(data=list(ReportSchedule.objects.filter(family_id=request.user.family_id).values()))
    def post(self, request):
        schedule = ReportSchedule.objects.create(family_id=request.user.family_id, created_by=request.user, report_type=request.data["report_type"], frequency=request.data["frequency"], filters=request.data.get("filters", {}), recipients=request.data.get("recipients", []), saved_report_id=request.data.get("saved_report"))
        return success_response(data={"id": str(schedule.id)}, message="Schedule created", status_code=201)

class ExportHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return success_response(data=list(ReportExportHistory.objects.filter(family_id=request.user.family_id, user=request.user).values()))
