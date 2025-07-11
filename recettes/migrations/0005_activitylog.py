# Generated by Django 5.1.5 on 2025-06-04 20:22

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "recettes",
            "0004_image_alter_categorie_image_alter_ingredient_image_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLog",
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
                    "action",
                    models.CharField(
                        choices=[
                            ("CREATE", "Ajouté"),
                            ("UPDATE", "Modifié"),
                            ("DELETE", "Supprimé"),
                        ],
                        max_length=10,
                        verbose_name="Action",
                    ),
                ),
                (
                    "model_type",
                    models.CharField(
                        choices=[
                            ("RECETTE", "Recette"),
                            ("INGREDIENT", "Ingrédient"),
                            ("CATEGORIE", "Catégorie"),
                        ],
                        max_length=20,
                        verbose_name="Type",
                    ),
                ),
                (
                    "object_name",
                    models.CharField(max_length=200, verbose_name="Nom de l'objet"),
                ),
                (
                    "object_id",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="ID de l'objet"
                    ),
                ),
                ("details", models.TextField(blank=True, verbose_name="Détails")),
                (
                    "timestamp",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Date et heure"
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True, null=True, verbose_name="Adresse IP"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Log d'activité",
                "verbose_name_plural": "Logs d'activité",
                "ordering": ["-timestamp"],
            },
        ),
    ]
