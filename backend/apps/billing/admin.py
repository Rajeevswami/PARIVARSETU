from django.contrib import admin

from .models import PaymentEvent, Plan, Subscription

admin.site.register(Plan)
admin.site.register(Subscription)
admin.site.register(PaymentEvent)
