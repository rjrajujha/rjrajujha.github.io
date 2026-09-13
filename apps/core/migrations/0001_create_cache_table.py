"""Create the shared Django cache table used for OTP challenges."""

from django.core.management import call_command
from django.db import migrations

from portfolio.cache_config import CACHE_TABLE


def create_cache_table(apps, schema_editor):
    # Shared across Gunicorn workers / serverless instances via Postgres.
    call_command("createcachetable", CACHE_TABLE, verbosity=0)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
