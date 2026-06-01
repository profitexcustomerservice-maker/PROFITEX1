from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_userplan_expires_at_userplan_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='badge_text',
            field=models.CharField(blank=True, help_text='Optional badge label such as Best value or Most popular', max_length=64, null=True),
        ),
    ]
