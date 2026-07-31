from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.common.response import success_response
from .models import AuditLog
class AuditLogView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,request):
  if request.user.role!="family_admin":raise PermissionDenied("Only family admins can view audit logs.")
  qs=AuditLog.objects.filter(family_id=request.user.family_id)
  for f in ("action","actor"):
   if request.query_params.get(f):qs=qs.filter(**{f:request.query_params[f]})
  return success_response(data=list(qs.values()[:500]))
