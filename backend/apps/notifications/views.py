from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from apps.common.response import success_response
from .models import Announcement, ActivityTimeline, Notification, NotificationPreference, SecurityEvent, LoginHistory
class NotificationViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request):
  qs=Notification.objects.filter(recipient=request.user,status="active")
  if request.query_params.get("is_read") is not None: qs=qs.filter(is_read=request.query_params["is_read"].lower()=="true")
  return success_response(data=list(qs.values()[:100]),meta={"unread_count":qs.filter(is_read=False).count()})
 @action(detail=True,methods=["post"])
 def read(self,request,pk=None): Notification.objects.filter(pk=pk,recipient=request.user).update(is_read=True,read_at=timezone.now()); return success_response(message="Notification marked as read")
 @action(detail=False,methods=["post"])
 def read_all(self,request): Notification.objects.filter(recipient=request.user,is_read=False).update(is_read=True,read_at=timezone.now()); return success_response(message="Notifications marked as read")
class PreferenceViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request):
  p,_=NotificationPreference.objects.get_or_create(user=request.user); return success_response(data={"in_app_enabled":p.in_app_enabled,"email_enabled":p.email_enabled,"push_enabled":p.push_enabled,"muted_types":p.muted_types})
 def create(self,request):
  p,_=NotificationPreference.objects.get_or_create(user=request.user)
  for f in ("in_app_enabled","email_enabled","push_enabled","muted_types"):
   if f in request.data:setattr(p,f,request.data[f])
  p.save();return self.list(request)
class TimelineViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request):
  qs=ActivityTimeline.objects.filter(family_id=request.user.family_id)
  if request.user.role!="family_admin" and hasattr(request.user,"member_profile"): qs=qs.filter(member=request.user.member_profile)
  for field in ("module","household","member"):
   if request.query_params.get(field):qs=qs.filter(**{field:request.query_params[field]})
  return success_response(data=list(qs.values()[:200]))
class AnnouncementViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request): return success_response(data=list(Announcement.objects.filter(family_id=request.user.family_id).values()))
 def create(self,request):
  if request.user.role!="family_admin":raise PermissionDenied("Only family admins can create announcements.")
  a=Announcement.objects.create(family_id=request.user.family_id,created_by=request.user,title=request.data["title"],description=request.data["description"],visibility=request.data.get("visibility","family"),start_date=request.data["start_date"],end_date=request.data.get("end_date") or None,attachment=request.FILES.get("attachment"));return success_response(data={"id":str(a.id)},status_code=201)
class SecurityViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request):
  if request.user.role=="family_admin":qs=SecurityEvent.objects.filter(member__family_id=request.user.family_id)
  else:qs=SecurityEvent.objects.filter(member=getattr(request.user,"member_profile",None))
  return success_response(data=list(qs.values()[:100]))
class LoginHistoryViewSet(viewsets.ViewSet):
 permission_classes=[permissions.IsAuthenticated]
 def list(self,request):
  qs=LoginHistory.objects.filter(member__family_id=request.user.family_id) if request.user.role=="family_admin" else LoginHistory.objects.filter(member=getattr(request.user,"member_profile",None)); return success_response(data=list(qs.values()[:100]))
