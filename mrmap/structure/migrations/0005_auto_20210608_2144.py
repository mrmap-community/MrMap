# Generated by Django 3.1.8 on 2021-06-08 19:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0004_auto_20210608_1923'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workflow',
            name='created_by_user',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='last_modified_by',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='owned_by_org',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
        migrations.DeleteModel(
            name='Workflow',
        ),
    ]
