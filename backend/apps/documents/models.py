import uuid
from django.conf import settings
from django.db import models

class DocumentCategory(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); family=models.ForeignKey("families.Family",on_delete=models.CASCADE,related_name="document_categories")
    name=models.CharField(max_length=100); description=models.TextField(blank=True); icon=models.CharField(max_length=50,blank=True); color=models.CharField(max_length=7,default="#64748b"); status=models.CharField(max_length=20,default="active"); sort_order=models.PositiveIntegerField(default=0); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table="documents_category"; ordering=["sort_order","name"]; constraints=[models.UniqueConstraint(fields=["family","name"],name="document_category_per_family")]

def stored_path(instance, filename):
    family_id = getattr(instance, "family_id", None) or instance.document.family_id
    return f"private/documents/{family_id}/{getattr(instance, "stored_filename", filename)}"
def number(): return f"DOC-{uuid.uuid4().hex[:10].upper()}"
class Document(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); document_number=models.CharField(max_length=30,unique=True,default=number,editable=False)
    family=models.ForeignKey("families.Family",on_delete=models.CASCADE,related_name="documents"); household=models.ForeignKey("households.Household",null=True,blank=True,on_delete=models.SET_NULL,related_name="documents"); owner=models.ForeignKey("members.Member",null=True,blank=True,on_delete=models.SET_NULL,related_name="owned_documents"); category=models.ForeignKey(DocumentCategory,null=True,blank=True,on_delete=models.SET_NULL,related_name="documents")
    title=models.CharField(max_length=200); description=models.TextField(blank=True); reference_type=models.CharField(max_length=30,blank=True); reference_id=models.UUIDField(null=True,blank=True); storage_provider=models.CharField(max_length=20,default="local"); original_filename=models.CharField(max_length=255); stored_filename=models.CharField(max_length=255); file=models.FileField(upload_to=stored_path); file_extension=models.CharField(max_length=15); mime_type=models.CharField(max_length=100); file_size=models.PositiveBigIntegerField(); checksum=models.CharField(max_length=64,db_index=True); version=models.PositiveIntegerField(default=1); is_latest=models.BooleanField(default=True); visibility=models.CharField(max_length=20,default="family"); status=models.CharField(max_length=20,default="active"); uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL,related_name="uploaded_documents"); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True); is_deleted=models.BooleanField(default=False,db_index=True)
    class Meta: db_table="documents_document"; ordering=["-created_at"]; indexes=[models.Index(fields=["family","category"]),models.Index(fields=["family","reference_type","reference_id"]),models.Index(fields=["household"]),models.Index(fields=["owner"])]
class DocumentVersion(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="versions"); version_number=models.PositiveIntegerField(); stored_filename=models.CharField(max_length=255); file=models.FileField(upload_to=stored_path); checksum=models.CharField(max_length=64); uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL,related_name="document_versions"); created_at=models.DateTimeField(auto_now_add=True); remarks=models.TextField(blank=True)
    class Meta: db_table="documents_version"; ordering=["-version_number"]; constraints=[models.UniqueConstraint(fields=["document","version_number"],name="document_version_number")]
class DocumentShare(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="shares"); shared_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="document_shares_made"); shared_with=models.ForeignKey("members.Member",on_delete=models.CASCADE,related_name="document_shares_received"); permission=models.CharField(max_length=20,default="read"); expiry_date=models.DateTimeField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table="documents_share"; constraints=[models.UniqueConstraint(fields=["document","shared_with"],name="document_shared_once_per_member")]
class DocumentAccessLog(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); document=models.ForeignKey(Document,on_delete=models.CASCADE,related_name="access_logs"); member=models.ForeignKey("members.Member",null=True,blank=True,on_delete=models.SET_NULL,related_name="document_access_logs"); action=models.CharField(max_length=20); ip_address=models.GenericIPAddressField(null=True,blank=True); device=models.CharField(max_length=255,blank=True); browser=models.CharField(max_length=255,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table="documents_access_log"; ordering=["-created_at"]; indexes=[models.Index(fields=["document","action","-created_at"])]
class StorageUsage(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); family=models.OneToOneField("families.Family",on_delete=models.CASCADE,related_name="storage_usage"); bytes_used=models.PositiveBigIntegerField(default=0); document_count=models.PositiveIntegerField(default=0); updated_at=models.DateTimeField(auto_now=True)
    class Meta: db_table="documents_storage_usage"

