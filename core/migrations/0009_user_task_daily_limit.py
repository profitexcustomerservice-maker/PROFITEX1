from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_systemsettings_support_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="usertask",
            name="completed_date",
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="usertask",
            unique_together={("user", "task", "completed_date")},
        ),
    ]
