from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_systemsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="support_phone",
            field=models.CharField(
                blank=True,
                help_text="Support phone or WhatsApp number",
                max_length=50,
                null=True,
            ),
        ),
    ]
