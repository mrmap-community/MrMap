# Generated by Django 3.2.7 on 2021-09-22 13:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('job', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('structure', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='created_by_user',
            field=models.ForeignKey(blank=True, editable=False, help_text='The user who has created this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_task_created_by_user', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AddField(
            model_name='task',
            name='job',
            field=models.ForeignKey(help_text='the parent task of this sub task', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', related_query_name='task', to='job.job', verbose_name='parent task'),
        ),
        migrations.AddField(
            model_name='task',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, editable=False, help_text='The last user who has modified this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_task_last_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Last modified by'),
        ),
        migrations.AddField(
            model_name='task',
            name='owned_by_org',
            field=models.ForeignKey(blank=True, editable=False, help_text='The organization which is the owner of this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_task_owned_by_org', to='structure.organization', verbose_name='Owner'),
        ),
        migrations.AddField(
            model_name='job',
            name='created_by_user',
            field=models.ForeignKey(blank=True, editable=False, help_text='The user who has created this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_job_created_by_user', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AddField(
            model_name='job',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, editable=False, help_text='The last user who has modified this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_job_last_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Last modified by'),
        ),
        migrations.AddField(
            model_name='job',
            name='owned_by_org',
            field=models.ForeignKey(blank=True, editable=False, help_text='The organization which is the owner of this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_job_owned_by_org', to='structure.organization', verbose_name='Owner'),
        ),
    ]
