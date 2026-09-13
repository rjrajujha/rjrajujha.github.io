import uuid

from django.db import models


class DeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"


class ContactSubmission(models.Model):
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # OTP challenge is persisted on the row so verification does not depend on
    # process-local cache or a missing cache table under multi-worker deploys.
    otp_challenge_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    otp_hash = models.CharField(max_length=64, blank=True, default="")
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)

    otp_verified = models.BooleanField(default=False)
    turnstile_verified = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    confirmation_sent = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=16,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        db_index=True,
    )

    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"{self.name} - {self.subject}"
