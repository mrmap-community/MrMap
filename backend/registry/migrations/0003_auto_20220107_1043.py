# Generated by Django 3.2.9 on 2022-01-07 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0002_auto_20220105_1336'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='catalougeserviceoperationurl',
            name='registry_catalougeserviceoperationurl_unique_together_method_id_operation',
        ),
        migrations.RemoveConstraint(
            model_name='webfeatureserviceoperationurl',
            name='registry_webfeatureserviceoperationurl_unique_together_method_id_operation',
        ),
        migrations.RemoveConstraint(
            model_name='webmapserviceoperationurl',
            name='registry_webmapserviceoperationurl_unique_together_method_id_operation',
        ),
        migrations.AddConstraint(
            model_name='webfeatureserviceoperationurl',
            constraint=models.UniqueConstraint(fields=('method', 'operation', 'service'), name='registry_webfeatureserviceoperationurl_unique_together_method_id_operation_service'),
        ),
        migrations.AddConstraint(
            model_name='webmapserviceoperationurl',
            constraint=models.UniqueConstraint(fields=('method', 'operation', 'service'), name='registry_webmapserviceoperationurl_unique_together_method_id_operation_service'),
        ),
    ]
