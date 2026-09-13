"""Add durable OTP challenge fields on ContactSubmission."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0003_contactsubmission_public_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactsubmission",
            name="otp_challenge_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="otp_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="otp_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="otp_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
