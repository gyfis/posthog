# Generated by Django 3.2.13 on 2022-06-14 13:58

import django.contrib.postgres.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0240_organizationinvite_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=100, null=True)),
                ("target_type", models.CharField(choices=[("email", "Email")], max_length=10)),
                ("target_value", models.TextField()),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("yearly", "Yearly"),
                        ],
                        max_length=10,
                    ),
                ),
                ("interval", models.IntegerField(default=1)),
                ("count", models.IntegerField(null=True)),
                (
                    "byweekday",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("monday", "Monday"),
                                ("tuesday", "Tuesday"),
                                ("wednesday", "Wednesday"),
                                ("thursday", "Thursday"),
                                ("friday", "Friday"),
                                ("saturday", "Saturday"),
                                ("sunday", "Sunday"),
                            ],
                            max_length=10,
                        ),
                        blank=True,
                        default=None,
                        null=True,
                        size=None,
                    ),
                ),
                ("bysetpos", models.IntegerField(null=True)),
                ("start_date", models.DateTimeField()),
                ("until_date", models.DateTimeField(blank=True, null=True)),
                ("next_delivery_date", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deleted", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "dashboard",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="posthog.dashboard"),
                ),
                (
                    "insight",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="posthog.insight"),
                ),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="posthog.team")),
            ],
        ),
    ]
