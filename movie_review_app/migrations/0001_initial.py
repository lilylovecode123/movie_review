# Generated by Django 4.1.7 on 2023-03-01 09:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Movies",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("movie_name", models.CharField(max_length=32)),
                ("movie_intro", models.CharField(max_length=256)),
                (
                    "release_time",
                    models.CharField(db_column="release_time", max_length=10),
                ),
                ("genre", models.CharField(max_length=20)),
                ("producer", models.CharField(max_length=10)),
                ("status", models.BooleanField(default=True)),
                (
                    "image",
                    models.TextField(
                        default="media/christopher-campbell-rDEOVtE7vOs-unsplash.jpg",
                        max_length=255,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "movies",
            },
        ),
        migrations.CreateModel(
            name="Users",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(max_length=32)),
                ("password", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=20)),
                ("email", models.EmailField(max_length=254)),
                (
                    "gender",
                    models.SmallIntegerField(choices=[(1, "Female"), (2, "Male")]),
                ),
                ("age", models.IntegerField()),
                ("type", models.IntegerField()),
                (
                    "avatar",
                    models.TextField(
                        default="media/christopher-campbell-rDEOVtE7vOs-unsplash.jpg",
                        max_length=255,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "users",
            },
        ),
        migrations.CreateModel(
            name="Admins",
            fields=[
                (
                    "user",
                    models.ForeignKey(
                        db_column="id",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="movie_review_app.users",
                    ),
                ),
                ("intro", models.CharField(max_length=125)),
                ("login_time", models.CharField(max_length=10)),
            ],
            options={
                "db_table": "admins",
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("num_coins", models.IntegerField()),
                ("num_followers", models.IntegerField()),
                (
                    "user",
                    models.ForeignKey(
                        db_column="id",
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="movie_review_app.users",
                    ),
                ),
                (
                    "movie",
                    models.ForeignKey(
                        db_column="movie_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="movie_review_app.movies",
                    ),
                ),
            ],
            options={
                "db_table": "user",
            },
        ),
        migrations.CreateModel(
            name="ReviewLogs",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("review_time", models.CharField(max_length=19)),
                ("comments", models.CharField(max_length=128)),
                ("ratings", models.IntegerField()),
                (
                    "commentedPerson",
                    models.IntegerField(db_column="commented_person", default=0),
                ),
                (
                    "movie",
                    models.ForeignKey(
                        db_column="movie_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="movie_review_app.movies",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="movie_review_app.user",
                    ),
                ),
            ],
            options={
                "db_table": "review_logs",
            },
        ),
        migrations.AddField(
            model_name="movies",
            name="admin",
            field=models.ForeignKey(
                db_column="admin_id",
                default="1",
                on_delete=django.db.models.deletion.CASCADE,
                to="movie_review_app.admins",
            ),
        ),
        migrations.CreateModel(
            name="FavoriateLists",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("collect_time", models.CharField(max_length=19)),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="movie_review_app.user",
                    ),
                ),
            ],
            options={
                "db_table": "favoriate_lists",
            },
        ),
    ]
