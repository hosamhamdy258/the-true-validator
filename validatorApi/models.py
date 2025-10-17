from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class APICallLog(models.Model):

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="api_call_logs")
    national_id = models.CharField(max_length=14)
    is_valid = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "API Call Log"
        verbose_name_plural = "API Call Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
        ]

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} - {self.national_id} - {self.timestamp}"
