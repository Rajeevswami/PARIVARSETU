from rest_framework import permissions,viewsets
from rest_framework.exceptions import PermissionDenied,ValidationError
from apps.common.response import success_response
from apps.audit.services.audit_service import record
from .models import ApplicationConfiguration,BackupHistory,FeatureFlag,FinancialYear,Lookup,RestoreHistory,SystemSetting
class AdminOnly(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def guard(self):
  if self.request.user.role!="family_admin":raise PermissionDenied("Family admin permission required.")
class SettingsView(AdminOnly):
 def list(self,request): self.guard(); return success_response(data=list(SystemSetting.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):
  self.guard(); s,_=SystemSetting.objects.update_or_create(family_id=request.user.family_id,key=request.data["key"],defaults={"value":request.data.get("value",{}),"module":request.data.get("module","general"),"updated_by":request.user});record(actor=request.user,action="setting_changed",family_id=request.user.family_id,metadata={"key":s.key});return success_response(data={"id":str(s.id)})
class FlagsView(AdminOnly):
 def list(self,request):self.guard();return success_response(data=list(FeatureFlag.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):
  self.guard();f,_=FeatureFlag.objects.update_or_create(family_id=request.user.family_id,key=request.data["key"],defaults={"enabled":request.data.get("enabled",True),"description":request.data.get("description", ""),"updated_by":request.user});record(actor=request.user,action="feature_enabled" if f.enabled else "feature_disabled",family_id=request.user.family_id,metadata={"key":f.key});return success_response(data={"id":str(f.id),"enabled":f.enabled})
class ConfigurationView(AdminOnly):
 def list(self,request):
  self.guard();c,_=ApplicationConfiguration.objects.get_or_create(family_id=request.user.family_id);return success_response(data={"storage_provider":c.storage_provider,"cache_provider":c.cache_provider,"logging_level":c.logging_level,"maintenance_mode":c.maintenance_mode,"maintenance_message":c.maintenance_message,"allowed_users":c.allowed_users})
 def create(self,request):
  self.guard();c,_=ApplicationConfiguration.objects.get_or_create(family_id=request.user.family_id)
  for f in ("email_config","sms_config","storage_provider","cache_provider","logging_level","maintenance_mode","maintenance_message","allowed_users"):
   if f in request.data:setattr(c,f,request.data[f])
  c.updated_by=request.user;c.save();record(actor=request.user,action="configuration_updated",family_id=request.user.family_id);return self.list(request)
class LookupView(AdminOnly):
 def list(self,request):self.guard();return success_response(data=list(Lookup.objects.filter(family_id=request.user.family_id,lookup_type=request.query_params.get("type","")).values()) if request.query_params.get("type") else list(Lookup.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):self.guard();o=Lookup.objects.create(family_id=request.user.family_id,lookup_type=request.data["lookup_type"],name=request.data["name"],code=request.data.get("code", ""));return success_response(data={"id":str(o.id)},status_code=201)
class FinancialYearView(AdminOnly):
 def list(self,request):self.guard();return success_response(data=list(FinancialYear.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):
  self.guard()
  if request.data["start_date"]>=request.data["end_date"]:raise ValidationError("Financial year end must follow its start.")
  if request.data.get("is_current"):FinancialYear.objects.filter(family_id=request.user.family_id,is_current=True).update(is_current=False)
  fy=FinancialYear.objects.create(family_id=request.user.family_id,**request.data);return success_response(data={"id":str(fy.id)},status_code=201)
class BackupView(AdminOnly):
 def list(self,request):self.guard();return success_response(data=list(BackupHistory.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):self.guard();b=BackupHistory.objects.create(family_id=request.user.family_id,backup_type=request.data.get("backup_type","full"),status="queued",created_by=request.user);record(actor=request.user,action="backup_created",family_id=request.user.family_id);return success_response(data={"id":str(b.id),"status":b.status},status_code=202)
class RestoreView(AdminOnly):
 def list(self,request):self.guard();return success_response(data=list(RestoreHistory.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):self.guard();r=RestoreHistory.objects.create(family_id=request.user.family_id,restore_type=request.data["restore_type"],backup_id=request.data.get("backup"),performed_by=request.user);record(actor=request.user,action="restore_performed",family_id=request.user.family_id);return success_response(data={"id":str(r.id),"status":r.status},status_code=202)
