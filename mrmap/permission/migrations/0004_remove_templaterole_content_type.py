# Generated by Django 3.1.7 on 2021-03-18 22:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('permission', '0003_auto_20210318_2131'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='templaterole',
            name='content_type',
        ),
    ]
