"""Add public UUID for contact submissions (create-after-Turnstile flow)."""

import uuid

from django.db import migrations, models


def backfill_public_ids(apps, schema_editor):
    ContactSubmission = apps.get_model("contact", "ContactSubmission")
    for row in ContactSubmission.objects.filter(public_id__isnull=True).iterator():
        row.public_id = uuid.uuid4()
        row.save(update_fields=["public_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0002_contact_submission_tracking"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactsubmission",
            name="public_id",
            field=models.UUIDField(db_index=True, editable=False, null=True),
        ),
        migrations.RunPython(backfill_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contactsubmission",
            name="public_id",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
