from django.contrib import admin
from .models import RenewalRecord, InquiryLog


@admin.register(RenewalRecord)
class RenewalRecordAdmin(admin.ModelAdmin):
    list_display = ("full_name", "national_id", "category", "school_name", "sector", "status_label", "is_published")
    list_filter = ("category", "sector", "status_label", "is_published")
    search_fields = ("full_name", "national_id", "school_name", "sector")
    list_per_page = 50


@admin.register(InquiryLog)
class InquiryLogAdmin(admin.ModelAdmin):
    list_display = ("national_id", "found", "ip_address", "created_at")
    list_filter = ("found", "created_at")
    search_fields = ("national_id", "ip_address")
    list_per_page = 50
