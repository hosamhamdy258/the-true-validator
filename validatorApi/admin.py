from django.contrib import admin

from .models import APICallLog


class APICallLogAdmin(admin.ModelAdmin):
    """Admin interface for API Call Logs"""

    list_display = [
        "timestamp",
        "user",
        "national_id",
        "is_valid",
        "ip_address",
    ]
    list_filter = ["is_valid", "timestamp", "user"]
    search_fields = ["national_id", "ip_address", "user__username"]
    readonly_fields = [
        "user",
        "national_id",
        "is_valid",
        "ip_address",
        "user_agent",
        "timestamp",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(APICallLog, APICallLogAdmin)
