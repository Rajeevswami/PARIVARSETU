from django.db.models import Count, Sum
from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from apps.common.response import success_response
from apps.common.permissions import IsFamilyAdmin
from .models import Document, DocumentCategory, DocumentShare, StorageUsage
from .services.document_service import can_access, log, new_version, upload

def data(doc): return {"id":str(doc.id),"document_number":doc.document_number,"title":doc.title,"description":doc.description,"original_filename":doc.original_filename,"file_size":doc.file_size,"mime_type":doc.mime_type,"version":doc.version,"visibility":doc.visibility,"status":doc.status,"reference_type":doc.reference_type,"reference_id":str(doc.reference_id or ""),"category":str(doc.category_id or ""),"created_at":doc.created_at}
class DocumentCategoryViewSet(viewsets.ModelViewSet):
    permission_classes=[permissions.IsAuthenticated]
    def get_queryset(self): return DocumentCategory.objects.filter(family_id=self.request.user.family_id)
    def list(self,request,*a,**k): return success_response(data=list(self.get_queryset().values()))
    def create(self,request,*a,**k):
        if request.user.role != "family_admin": raise PermissionDenied("Only family admins can manage categories.")
        c=DocumentCategory.objects.create(family_id=request.user.family_id,**request.data); return success_response(data={"id":str(c.id)},status_code=201)
class DocumentViewSet(viewsets.ViewSet):
    permission_classes=[permissions.IsAuthenticated]
    def queryset(self): return Document.objects.filter(family_id=self.request.user.family_id,is_deleted=False).select_related("category","owner","household")
    def list(self,request):
        qs=self.queryset()
        for field in ("category","household","owner","visibility","status","reference_type"):
            if request.query_params.get(field): qs=qs.filter(**{field:request.query_params[field]})
        if request.query_params.get("search"):
            from django.db.models import Q
            q=request.query_params["search"]; qs=qs.filter(Q(document_number__icontains=q)|Q(title__icontains=q)|Q(original_filename__icontains=q))
        return success_response(data=[data(d) for d in qs[:100]])
    def retrieve(self,request,pk=None):
        doc=self.queryset().get(pk=pk)
        if not can_access(request.user,doc): raise PermissionDenied("You cannot view this document.")
        log(doc,request.user,"view",request); result=data(doc); result["versions"]=list(doc.versions.values("id","version_number","stored_filename","checksum","created_at","remarks")); return success_response(data=result)
    def create(self,request):
        files=request.FILES.getlist("files") or ([request.FILES["file"]] if "file" in request.FILES else [])
        if not files: return success_response(message="At least one file is required",status_code=400)
        return success_response(data=[data(upload(user=request.user,file=f,data=request.data)) for f in files],message="Documents uploaded",status_code=201)
    def partial_update(self,request,pk=None):
        doc=self.queryset().get(pk=pk)
        if not can_access(request.user,doc,True): raise PermissionDenied("You cannot update this document.")
        for field in ("title","description","category","household","owner","visibility","status","reference_type","reference_id"):
            if field in request.data: setattr(doc,f"{field}_id" if field in ("category","household","owner") else field,request.data[field] or None)
        doc.save(); log(doc,request.user,"update",request); return success_response(data=data(doc))
    def destroy(self,request,pk=None):
        doc=self.queryset().get(pk=pk)
        if not can_access(request.user,doc,True): raise PermissionDenied("You cannot delete this document.")
        doc.is_deleted=True; doc.status="deleted"; doc.save(update_fields=["is_deleted","status"]); log(doc,request.user,"delete",request); return success_response(message="Document deleted")
    @action(detail=True,methods=["post"])
    def version(self,request,pk=None): return success_response(data=data(new_version(user=request.user,document=self.queryset().get(pk=pk),file=request.FILES["file"],remarks=request.data.get("remarks",""))))
    @action(detail=True,methods=["get"])
    def download(self,request,pk=None):
        doc=self.queryset().get(pk=pk)
        if not can_access(request.user,doc): raise PermissionDenied("You cannot download this document.")
        log(doc,request.user,"download",request); return FileResponse(doc.file.open("rb"),as_attachment=True,filename=doc.original_filename)
    @action(detail=True,methods=["post"])
    def share(self,request,pk=None):
        doc=self.queryset().get(pk=pk)
        if not can_access(request.user,doc,True): raise PermissionDenied("You cannot share this document.")
        share,_=DocumentShare.objects.update_or_create(document=doc,shared_with_id=request.data["member"],defaults={"shared_by":request.user,"permission":request.data.get("permission","read"),"expiry_date":request.data.get("expiry_date") or None}); log(doc,request.user,"share",request); return success_response(data={"id":str(share.id)})
    @action(detail=True,methods=["post"])
    def restore(self,request,pk=None):
        doc=Document.objects.get(pk=pk,family_id=request.user.family_id,is_deleted=True)
        if not can_access(request.user,doc,True): raise PermissionDenied("You cannot restore this document.")
        doc.is_deleted=False; doc.status="active"; doc.save(update_fields=["is_deleted","status"]); log(doc,request.user,"restore",request); return success_response(data=data(doc))
class StorageView(viewsets.ViewSet):
    permission_classes=[permissions.IsAuthenticated]
    def list(self,request):
        usage,_=StorageUsage.objects.get_or_create(family_id=request.user.family_id); return success_response(data={"bytes_used":usage.bytes_used,"document_count":usage.document_count,"by_category":list(Document.objects.filter(family_id=request.user.family_id,is_deleted=False).values("category__name").annotate(count=Count("id"),bytes=Sum("file_size")))})
