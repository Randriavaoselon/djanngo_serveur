# Generated by Django 5.1.3 on 2024-12-07 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serveur', '0003_clientinfo_screenshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientinfo',
            name='nom_client',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
