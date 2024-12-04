# Generated by Django 5.1.2 on 2024-12-04 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notify', '0003_alter_backgroundprocess_process_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundprocess',
            name='done_steps',
            field=models.IntegerField(default=-1, help_text='done steps of processing', verbose_name='done'),
        ),
        migrations.AddField(
            model_name='backgroundprocess',
            name='total_steps',
            field=models.IntegerField(default=0, help_text='total steps of processing', verbose_name='total'),
        ),
    ]
