# Generated by Django 5.1.7 on 2025-03-21 12:08

import notify.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notify', '0010_alter_backgroundprocess_celery_task_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundprocesslog',
            name='extented_description',
            field=models.FileField(help_text='this can be the response content for example', null=True, upload_to=notify.models.extented_description_file_path, verbose_name='Extented Description'),
        ),
    ]
