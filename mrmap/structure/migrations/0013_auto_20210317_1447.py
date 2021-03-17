# Generated by Django 3.1.7 on 2021-03-17 13:47

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0012_auto_20210316_0904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupinvitationrequest',
            name='activation_until',
            field=models.DateTimeField(default=datetime.datetime(2021, 4, 16, 13, 47, 9, 269957, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='publishrequest',
            name='activation_until',
            field=models.DateTimeField(default=datetime.datetime(2021, 4, 16, 13, 47, 9, 269957, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='useractivation',
            name='activation_until',
            field=models.DateTimeField(default=datetime.datetime(2021, 4, 16, 13, 47, 9, 267831, tzinfo=utc)),
        ),
    ]
