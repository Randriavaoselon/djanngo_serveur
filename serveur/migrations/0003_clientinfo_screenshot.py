# Generated by Django 5.1.3 on 2024-12-06 14:03

import serveur.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serveur', '0002_alter_clientinfo_ip_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientinfo',
            name='screenshot',
            field=models.ImageField(blank=True, null=True, upload_to=serveur.models.client_screenshot_upload_path),
        ),
    ]
