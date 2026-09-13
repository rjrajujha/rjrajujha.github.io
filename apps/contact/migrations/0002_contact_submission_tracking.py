# Generated manually for contact submission tracking

from django.db import migrations, models


def copy_sent_to_email(apps, schema_editor):
    ContactSubmission = apps.get_model("contact", "ContactSubmission")
    for row in ContactSubmission.objects.all().order_by("id"):
        if getattr(row, "sent_to_email", False):
            row.email_sent = True
            row.delivery_status = "delivered"
            row.save(update_fields=["email_sent", "delivery_status"])


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="contactsubmission",
            old_name="created_at",
            new_name="submitted_at",
        ),
        migrations.AlterModelOptions(
            name="contactsubmission",
            options={"ordering": ["-submitted_at"]},
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="confirmation_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="delivery_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("delivered", "Delivered"),
                    ("failed", "Failed"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="email_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="otp_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="turnstile_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="contactsubmission",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(copy_sent_to_email, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="contactsubmission",
            name="sent_to_email",
        ),
        migrations.AlterField(
            model_name="contactsubmission",
            name="submitted_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
