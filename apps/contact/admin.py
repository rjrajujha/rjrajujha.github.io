from django.apps import apps
from django.contrib import admin

from .models import ContactSubmission


class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "subject",
        "name",
        "email",
        "delivery_status",
        "otp_verified",
        "turnstile_verified",
        "email_sent",
        "confirmation_sent",
        "submitted_at",
        "verified_at",
    )
    list_filter = (
        "delivery_status",
        "otp_verified",
        "turnstile_verified",
        "email_sent",
        "confirmation_sent",
        "submitted_at",
    )
    search_fields = ("public_id", "name", "email", "subject", "message")
    readonly_fields = (
        "public_id",
        "name",
        "email",
        "subject",
        "message",
        "ip_address",
        "user_agent",
        "otp_verified",
        "turnstile_verified",
        "otp_challenge_id",
        "otp_expires_at",
        "otp_attempts",
        "email_sent",
        "confirmation_sent",
        "delivery_status",
        "submitted_at",
        "verified_at",
        "delivered_at",
    )
    ordering = ("-submitted_at",)

    fieldsets = (
        ("Message", {"fields": ("public_id", "name", "email", "subject", "message")}),
        (
            "Verification & delivery",
            {
                "fields": (
                    "otp_verified",
                    "turnstile_verified",
                    "otp_challenge_id",
                    "otp_expires_at",
                    "otp_attempts",
                    "delivery_status",
                    "email_sent",
                    "confirmation_sent",
                    "submitted_at",
                    "verified_at",
                    "delivered_at",
                )
            },
        ),
        ("Audit", {"fields": ("ip_address", "user_agent")}),
    )

    def has_add_permission(self, request):
        return False


if apps.is_installed("django.contrib.admin"):
    admin.site.register(ContactSubmission, ContactSubmissionAdmin)
