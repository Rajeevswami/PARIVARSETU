from django.core.cache import cache

def scoped_key(namespace, *, family_id=None, user_id=None, suffix=""):
 parts=["parivarsetu",namespace,str(family_id or "global"),str(user_id or "shared"),suffix]
 return ":".join(part for part in parts if part)
def get_or_set(namespace, factory, *, family_id=None, user_id=None, suffix="", timeout=60):
 key=scoped_key(namespace,family_id=family_id,user_id=user_id,suffix=suffix)
 return cache.get_or_set(key,factory,timeout)
def invalidate(namespace, *, family_id=None, user_id=None):
 # Version keys allow invalidation without Redis key scans.
 version_key=scoped_key(f"{namespace}:version",family_id=family_id,user_id=user_id)
 try:cache.incr(version_key)
 except ValueError:cache.set(version_key,1,None)
def version(namespace, *, family_id=None, user_id=None):
 return cache.get_or_set(scoped_key(f"{namespace}:version",family_id=family_id,user_id=user_id),lambda:1,None)
