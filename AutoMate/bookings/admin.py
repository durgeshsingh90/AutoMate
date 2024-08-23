# bookings/admin.py
from django.contrib import admin
from .models import Scheme, SchemeType
import logging

logger = logging.getLogger(__name__)

class SchemeTypeInline(admin.TabularInline):
    model = SchemeType
    extra = 1  # Number of extra forms displayed in the admin interface for related SchemeTypes

class SchemeAdmin(admin.ModelAdmin):
    inlines = [SchemeTypeInline]
    list_display = ('name',)
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        logger.info(f"Saving {obj} with change status {change}")
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        logger.info(f"Deleting {obj}")
        super().delete_model(request, obj)

admin.site.register(Scheme, SchemeAdmin)
