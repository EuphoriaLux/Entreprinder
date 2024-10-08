# Generated by Django 5.0.6 on 2024-08-04 21:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Industry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="EntrepreneurProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "profile_picture",
                    models.ImageField(blank=True, null=True, upload_to="profile_pics"),
                ),
                ("bio", models.TextField(blank=True, max_length=500)),
                (
                    "tagline",
                    models.CharField(
                        blank=True,
                        help_text="A brief, catchy description of yourself",
                        max_length=150,
                    ),
                ),
                ("company", models.CharField(blank=True, max_length=100)),
                ("looking_for", models.TextField(blank=True, max_length=500)),
                (
                    "offering",
                    models.TextField(
                        blank=True,
                        help_text="What can you offer to other entrepreneurs?",
                        max_length=500,
                    ),
                ),
                ("location", models.CharField(max_length=100)),
                ("website", models.URLField(blank=True)),
                ("linkedin_profile", models.URLField(blank=True)),
                ("years_of_experience", models.PositiveIntegerField(default=0)),
                ("is_mentor", models.BooleanField(default=False)),
                ("is_looking_for_funding", models.BooleanField(default=False)),
                ("is_investor", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "industry",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="entreprinder.industry",
                    ),
                ),
                (
                    "skills",
                    models.ManyToManyField(
                        related_name="entrepreneurs", to="entreprinder.skill"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "liked",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes_received",
                        to="entreprinder.entrepreneurprofile",
                    ),
                ),
                (
                    "liker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes_given",
                        to="entreprinder.entrepreneurprofile",
                    ),
                ),
            ],
            options={
                "unique_together": {("liker", "liked")},
            },
        ),
        migrations.CreateModel(
            name="Match",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "entrepreneur1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matches_as_first",
                        to="entreprinder.entrepreneurprofile",
                    ),
                ),
                (
                    "entrepreneur2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matches_as_second",
                        to="entreprinder.entrepreneurprofile",
                    ),
                ),
            ],
            options={
                "unique_together": {("entrepreneur1", "entrepreneur2")},
            },
        ),
    ]
