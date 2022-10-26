# Generated by Django 3.2.15 on 2022-09-30 09:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import posthog.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0261_team_capture_console_log_opt_in"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationViewed",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=posthog.models.utils.UUIDT, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("last_viewed_activity_date", models.DateTimeField(default=None)),
                (
                    "user",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="notificationviewed",
            constraint=models.UniqueConstraint(fields=("user",), name="posthog_user_unique_viewed_date"),
        ),
    ]
