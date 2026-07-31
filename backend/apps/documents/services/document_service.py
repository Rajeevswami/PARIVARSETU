import hashlib, os, uuid
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.audit.services.audit_service import record
from ..models import Document, DocumentAccessLog, DocumentVersion, StorageUsage
ALLOWED={"pdf","png","jpg","jpeg","webp","csv","xlsx","docx"}; MAX_SIZE=getattr(settings,"DOCUMENT_MAX_FILE_SIZE",20*1024*1024)
def checksum(file):
    value=hashlib.sha256()
    for chunk in file.chunks(): value.update(chunk)
    file.seek(0); return value.hexdigest()
def validate(file):
    extension=os.path.splitext(file.name)[1].lower().lstrip(".")
    if extension not in ALLOWED: raise ValidationError("This file type is not allowed.")
    if file.size > MAX_SIZE: raise ValidationError(f"File exceeds the {MAX_SIZE} byte limit.")
    return extension
def can_access(user, document, write=False):
    if user.role == "family_admin": return user.family_id == document.family_id
    if user.family_id != document.family_id: return False
    member=getattr(user,"member_profile",None)
    if document.visibility == "admin_only": return False
    if document.visibility == "private" and document.owner_id != getattr(member,"id",None) and document.uploaded_by_id != user.id: return False
    share=document.shares.filter(shared_with=member).filter(expiry_date__isnull=True)|document.shares.filter(shared_with=member,expiry_date__gt=timezone.now()) if member else document.shares.none()
    return not write or document.uploaded_by_id == user.id or share.filter(permission__in=["update","admin"]).exists()
def log(document,user,action,request=None):
    member=getattr(user,"member_profile",None); DocumentAccessLog.objects.create(document=document,member=member,action=action,ip_address=(request.META.get("REMOTE_ADDR") if request else None),browser=(request.META.get("HTTP_USER_AGENT","")[:255] if request else "")); record(actor=user,action=f"document_{action}",target_model="Document",target_id=document.id,family_id=document.family_id)
@transaction.atomic
def upload(*,user,file,data):
    ext=validate(file); digest=checksum(file); family_id=user.family_id
    duplicate=Document.objects.filter(family_id=family_id,checksum=digest,is_deleted=False).first()
    if duplicate: raise ValidationError({"file":"An identical document already exists.","document_id":str(duplicate.id)})
    stored=f"{uuid.uuid4().hex}.{ext}"; doc=Document.objects.create(family_id=family_id,household_id=data.get("household"),owner_id=data.get("owner"),category_id=data.get("category"),title=data.get("title") or file.name,description=data.get("description", ""),reference_type=data.get("reference_type", ""),reference_id=data.get("reference_id") or None,original_filename=file.name,stored_filename=stored,file=file,file_extension=ext,mime_type=getattr(file,"content_type","") or "application/octet-stream",file_size=file.size,checksum=digest,visibility=data.get("visibility","family"),uploaded_by=user)
    StorageUsage.objects.update_or_create(family_id=family_id,defaults={})
    usage=StorageUsage.objects.select_for_update().get(family_id=family_id); usage.bytes_used+=file.size; usage.document_count+=1; usage.save()
    log(doc,user,"upload"); return doc
@transaction.atomic
def new_version(*,user,document,file,remarks=""):
    if not can_access(user,document,True): raise PermissionDenied("You cannot version this document.")
    ext=validate(file); digest=checksum(file); version=document.version+1; stored=f"{uuid.uuid4().hex}.{ext}"
    DocumentVersion.objects.create(document=document,version_number=document.version,stored_filename=document.stored_filename,file=document.file,checksum=document.checksum,uploaded_by=document.uploaded_by,remarks="Previous current version")
    document.file=file; document.stored_filename=stored; document.file_extension=ext; document.mime_type=getattr(file,"content_type","") or document.mime_type; document.file_size=file.size; document.checksum=digest; document.version=version; document.uploaded_by=user; document.save(); log(document,user,"version_created"); return document
