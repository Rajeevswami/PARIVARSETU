import hashlib
from django.http import HttpResponseNotModified
from django.utils.deprecation import MiddlewareMixin
class ConditionalGetMiddleware(MiddlewareMixin):
 """Adds strong ETags to cacheable API GET responses without caching private data."""
 def process_response(self,request,response):
  if request.method!="GET" or response.status_code!=200 or response.streaming or "ETag" in response:return response
  if not response.get("Content-Type","").startswith("application/json"):return response
  etag='"'+hashlib.sha256(response.content).hexdigest()+'"';response["ETag"]=etag;response["Cache-Control"]="private, max-age=30, must-revalidate"
  if request.headers.get("If-None-Match")==etag:
   not_modified=HttpResponseNotModified();not_modified["ETag"]=etag;not_modified["Cache-Control"]=response["Cache-Control"];return not_modified
  return response
