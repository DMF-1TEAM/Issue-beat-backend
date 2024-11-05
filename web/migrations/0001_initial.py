# Generated by Django 5.0.7 on 2024-10-31 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="News",
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
                ("date", models.DateField()),
                ("title", models.CharField(max_length=100)),
                ("press", models.CharField(max_length=20)),
                ("author", models.CharField(max_length=20)),
                ("content", models.TextField()),
                ("keyword", models.TextField()),
                ("image", models.TextField()),
                ("link", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="NewsAnalysis",
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
                ("keyword", models.CharField(max_length=100)),
                ("background", models.TextField()),
                ("core_content", models.TextField()),
                ("conclusion", models.TextField()),
                ("article_count", models.IntegerField()),
                ("processed_article_count", models.IntegerField()),
                ("chunk_count", models.IntegerField()),
                ("processed_at", models.DateTimeField()),
                ("date_range_start", models.DateField()),
                ("date_range_end", models.DateField()),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["keyword"], name="web_newsana_keyword_9a7433_idx"
                    ),
                    models.Index(
                        fields=["processed_at"], name="web_newsana_process_cf1372_idx"
                    ),
                ],
            },
        ),
    ]