import os

from celery import Celery

from config.product import PRODUCT_SLUG

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery(PRODUCT_SLUG)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
