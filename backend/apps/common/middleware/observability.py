import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin
logger=logging.getLogger("apps.performance")
class RequestObservabilityMiddleware(MiddlewareMixin):
 def process_request(self,request):
  request.request_id=request.headers.get("X-Request-ID",str(uuid.uuid4()));request._started_at=time.perf_counter()
 def process_response(self,request,response):
  request_id=getattr(request,"request_id",None)
  if request_id:response["X-Request-ID"]=request_id
  started=getattr(request,"_started_at",None)
  if started is not None:
   elapsed=(time.perf_counter()-started)*1000;response["X-Response-Time-Ms"]=f"{elapsed:.1f}"
   if elapsed>500: logger.warning("slow_request request_id=%s path=%s status=%s duration_ms=%.1f",request_id,request.path,response.status_code,elapsed)
  return response
class SecurityHeadersMiddleware(MiddlewareMixin):
 def process_response(self,request,response):
  response.setdefault("X-Content-Type-Options","nosniff");response.setdefault("X-Frame-Options","DENY");response.setdefault("Referrer-Policy","strict-origin-when-cross-origin");response.setdefault("Permissions-Policy","camera=(), microphone=(), geolocation=()");return response
