from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("reward", models.DecimalField(decimal_places=2, max_digits=10)),
                ("media", models.FileField(blank=True, null=True, upload_to="tasks/%Y/%m")),
                ("media_type", models.CharField(choices=[("image", "Image"), ("video", "Video")], default="image", max_length=10)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("reward", models.DecimalField(decimal_places=2, max_digits=10)),
                ("duration_days", models.PositiveSmallIntegerField(default=7)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="UserTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="completions", to="core.task")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="completed_tasks", to="accounts.user")),
            ],
            options={"ordering": ["-completed_at"], "unique_together": {("user", "task")}},
        ),
        migrations.CreateModel(
            name="UserPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to="core.plan")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="plans", to="accounts.user")),
            ],
            options={"ordering": ["-joined_at"], "unique_together": {("user", "plan")}},
        ),
    ]
