# Generated by Django 3.2.7 on 2021-09-22 13:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('registry', '0001_initial'),
        ('django_celery_beat', '0015_edit_solarschedule_events_choices'),
        ('monitoring', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringsetting',
            name='metadatas',
            field=models.ManyToManyField(related_name='monitoring_setting', to='registry.Service'),
        ),
        migrations.AddField(
            model_name='monitoringsetting',
            name='periodic_task',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.periodictask'),
        ),
    ]
