# Generated by Django 5.1.2 on 2024-11-25 16:37

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0019_alter_periodictasks_options'),
        ('django_celery_results', '0011_taskresult_periodic_task_name'),
        ('registry', '0003_keyword_registry_keyword_non_empty_keywords'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layergetmapresult',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='layergetmapresult',
            name='task_result',
        ),
        migrations.RemoveField(
            model_name='wmsgetcapabilitiesresult',
            name='service',
        ),
        migrations.RemoveField(
            model_name='wmsgetcapabilitiesresult',
            name='task_result',
        ),
        migrations.AlterField(
            model_name='catalogueservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='catalogueservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='catalogueserviceoperationurl',
            name='mime_types',
            field=models.ManyToManyField(blank=True, help_text='all available mime types of the remote url', related_name='%(class)s_operation_urls', related_query_name='%(class)s_operation_url', to='registry.mimetype', verbose_name='internet mime type'),
        ),
        migrations.AlterField(
            model_name='catalogueserviceoperationurl',
            name='operation',
            field=models.CharField(choices=[('GetCapabilities', 'Get Capabilities'), ('GetMap', 'Get Map'), ('GetFeatureInfo', 'Get Feature Info'), ('DescribeLayer', 'Describe Layer'), ('GetLegendGraphic', 'Get Legend Graphic'), ('GetStyles', 'Get Styles'), ('PutStyles', 'Put Styles'), ('GetFeature', 'Get Feature'), ('Transaction', 'Transaction'), ('LockFeature', 'Lock Feature'), ('DescribeFeatureType', 'Describe Feature Type'), ('GetFeatureWithLock', 'Get Feature With Lock'), ('GetGmlObject', 'Get Gml Object'), ('ListStoredQueries', 'List Stored Queries'), ('GetPropertyValue', 'Get Property Value'), ('DescribeStoredQueries', 'Describe Stored Queries'), ('GetRecords', 'Get Records'), ('DescribeRecord', 'Describe Record'), ('GetRecordById', 'Get Record By Id')], help_text='the operation you can perform with this url.', max_length=30, verbose_name='operation'),
        ),
        migrations.AlterField(
            model_name='catalogueserviceoperationurl',
            name='url',
            field=models.URLField(help_text='the url for this operation', max_length=4096, verbose_name='url'),
        ),
        migrations.AlterField(
            model_name='datasetmetadatarecord',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='datasetmetadatarecord',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='featuretype',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='featuretype',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicalcatalogueservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicalcatalogueservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicaldatasetmetadatarecord',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicaldatasetmetadatarecord',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicalfeaturetype',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicalfeaturetype',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicallayer',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicallayer',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicalservicemetadatarecord',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicalservicemetadatarecord',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicalwebfeatureservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicalwebfeatureservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='historicalwebmapservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='historicalwebmapservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='servicemetadatarecord',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='servicemetadatarecord',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='webfeatureservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='webfeatureservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='webfeatureserviceoperationurl',
            name='mime_types',
            field=models.ManyToManyField(blank=True, help_text='all available mime types of the remote url', related_name='%(class)s_operation_urls', related_query_name='%(class)s_operation_url', to='registry.mimetype', verbose_name='internet mime type'),
        ),
        migrations.AlterField(
            model_name='webfeatureserviceoperationurl',
            name='operation',
            field=models.CharField(choices=[('GetCapabilities', 'Get Capabilities'), ('GetMap', 'Get Map'), ('GetFeatureInfo', 'Get Feature Info'), ('DescribeLayer', 'Describe Layer'), ('GetLegendGraphic', 'Get Legend Graphic'), ('GetStyles', 'Get Styles'), ('PutStyles', 'Put Styles'), ('GetFeature', 'Get Feature'), ('Transaction', 'Transaction'), ('LockFeature', 'Lock Feature'), ('DescribeFeatureType', 'Describe Feature Type'), ('GetFeatureWithLock', 'Get Feature With Lock'), ('GetGmlObject', 'Get Gml Object'), ('ListStoredQueries', 'List Stored Queries'), ('GetPropertyValue', 'Get Property Value'), ('DescribeStoredQueries', 'Describe Stored Queries'), ('GetRecords', 'Get Records'), ('DescribeRecord', 'Describe Record'), ('GetRecordById', 'Get Record By Id')], help_text='the operation you can perform with this url.', max_length=30, verbose_name='operation'),
        ),
        migrations.AlterField(
            model_name='webfeatureserviceoperationurl',
            name='url',
            field=models.URLField(help_text='the url for this operation', max_length=4096, verbose_name='url'),
        ),
        migrations.AlterField(
            model_name='webfeatureserviceproxysetting',
            name='secured_service',
            field=models.OneToOneField(help_text='the security proxy settings for this service.', on_delete=django.db.models.deletion.CASCADE, related_name='proxy_setting', related_query_name='proxy_setting', to='registry.webfeatureservice', verbose_name='service'),
        ),
        migrations.AlterField(
            model_name='webmapservice',
            name='abstract',
            field=models.TextField(blank=True, default='', help_text='brief summary of the content of this metadata.', verbose_name='abstract'),
        ),
        migrations.AlterField(
            model_name='webmapservice',
            name='insufficient_quality',
            field=models.TextField(blank=True, default='', editable=False, help_text='TODO'),
        ),
        migrations.AlterField(
            model_name='webmapserviceoperationurl',
            name='mime_types',
            field=models.ManyToManyField(blank=True, help_text='all available mime types of the remote url', related_name='%(class)s_operation_urls', related_query_name='%(class)s_operation_url', to='registry.mimetype', verbose_name='internet mime type'),
        ),
        migrations.AlterField(
            model_name='webmapserviceoperationurl',
            name='operation',
            field=models.CharField(choices=[('GetCapabilities', 'Get Capabilities'), ('GetMap', 'Get Map'), ('GetFeatureInfo', 'Get Feature Info'), ('DescribeLayer', 'Describe Layer'), ('GetLegendGraphic', 'Get Legend Graphic'), ('GetStyles', 'Get Styles'), ('PutStyles', 'Put Styles'), ('GetFeature', 'Get Feature'), ('Transaction', 'Transaction'), ('LockFeature', 'Lock Feature'), ('DescribeFeatureType', 'Describe Feature Type'), ('GetFeatureWithLock', 'Get Feature With Lock'), ('GetGmlObject', 'Get Gml Object'), ('ListStoredQueries', 'List Stored Queries'), ('GetPropertyValue', 'Get Property Value'), ('DescribeStoredQueries', 'Describe Stored Queries'), ('GetRecords', 'Get Records'), ('DescribeRecord', 'Describe Record'), ('GetRecordById', 'Get Record By Id')], help_text='the operation you can perform with this url.', max_length=30, verbose_name='operation'),
        ),
        migrations.AlterField(
            model_name='webmapserviceoperationurl',
            name='service',
            field=models.ForeignKey(help_text='the web map service for that this url can be used for.', on_delete=django.db.models.deletion.CASCADE, related_name='operation_urls', related_query_name='operation_url', to='registry.webmapservice', verbose_name='related web map service'),
        ),
        migrations.AlterField(
            model_name='webmapserviceoperationurl',
            name='url',
            field=models.URLField(help_text='the url for this operation', max_length=4096, verbose_name='url'),
        ),
        migrations.AlterField(
            model_name='webmapserviceproxysetting',
            name='secured_service',
            field=models.OneToOneField(help_text='the security proxy settings for this service.', on_delete=django.db.models.deletion.CASCADE, related_name='proxy_setting', related_query_name='proxy_setting', to='registry.webmapservice', verbose_name='service'),
        ),
        migrations.CreateModel(
            name='WebMapServiceMonitoringRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Datetime field when the run was created in UTC', null=True, verbose_name='Created DateTime')),
                ('date_done', models.DateTimeField(auto_now_add=True, help_text='Datetime field when the run was done in UTC', null=True, verbose_name='Done DateTime')),
                ('group_result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_results.groupresult')),
            ],
        ),
        migrations.CreateModel(
            name='GetMapProbeResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_code', models.IntegerField(blank=True, default=None, editable=False, help_text='The http status code of the response', null=True, verbose_name='HTTP status code')),
                ('monitored_uri', models.URLField(editable=False, help_text='This is the url which was monitored', max_length=4096, verbose_name='monitored uri')),
                ('request_duration', models.DurationField(blank=True, editable=False, help_text='elapsed time of the request', null=True, verbose_name='request duration')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Datetime field when the task result was created in UTC', verbose_name='Created DateTime')),
                ('date_done', models.DateTimeField(blank=True, help_text='Datetime field when the task was completed in UTC', null=True, verbose_name='Completed DateTime')),
                ('check_response_image_success', models.BooleanField(blank=True, default=None, null=True)),
                ('check_response_image_message', models.TextField(blank=True, default=None, null=True)),
                ('check_response_does_not_contain_success', models.BooleanField(blank=True, default=None, null=True)),
                ('check_response_does_not_contain_message', models.TextField(blank=True, default=None, null=True)),
                ('celery_task_result', models.OneToOneField(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_results.taskresult')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s', to='registry.webmapservicemonitoringrun', verbose_name='Run')),
            ],
            options={
                'ordering': ['-date_done'],
                'get_latest_by': 'date_done',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GetCapabilitiesProbeResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_code', models.IntegerField(blank=True, default=None, editable=False, help_text='The http status code of the response', null=True, verbose_name='HTTP status code')),
                ('monitored_uri', models.URLField(editable=False, help_text='This is the url which was monitored', max_length=4096, verbose_name='monitored uri')),
                ('request_duration', models.DurationField(blank=True, editable=False, help_text='elapsed time of the request', null=True, verbose_name='request duration')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Datetime field when the task result was created in UTC', verbose_name='Created DateTime')),
                ('date_done', models.DateTimeField(blank=True, help_text='Datetime field when the task was completed in UTC', null=True, verbose_name='Completed DateTime')),
                ('check_response_is_valid_xml_success', models.BooleanField(blank=True, default=None, null=True)),
                ('check_response_is_valid_xml_message', models.TextField(blank=True, default=None, null=True)),
                ('check_response_does_not_contain_success', models.BooleanField(blank=True, default=None, null=True)),
                ('check_response_does_not_contain_message', models.TextField(blank=True, default=None, null=True)),
                ('check_response_does_contain_success', models.BooleanField(blank=True, default=None, null=True)),
                ('check_response_does_contain_message', models.TextField(blank=True, default=None, null=True)),
                ('celery_task_result', models.OneToOneField(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_results.taskresult')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s', to='registry.webmapservicemonitoringrun', verbose_name='Run')),
            ],
            options={
                'ordering': ['-date_done'],
                'get_latest_by': 'date_done',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WebMapServiceMonitoringSetting',
            fields=[
                ('periodictask_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='django_celery_beat.periodictask')),
                ('service', models.ForeignKey(help_text='this is the service which shall be monitored', on_delete=django.db.models.deletion.CASCADE, related_name='web_map_service_monitorings', related_query_name='web_map_service_monitoring', to='registry.webmapservice', verbose_name='web map service')),
            ],
            bases=('django_celery_beat.periodictask',),
        ),
        migrations.AddField(
            model_name='webmapservicemonitoringrun',
            name='setting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='registry.webmapservicemonitoringsetting'),
        ),
        migrations.CreateModel(
            name='GetMapProbe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeout', models.IntegerField(blank=True, default=30)),
                ('check_response_does_not_contain', models.CharField(blank=True, default='ExceptionReport>, ServiceException>', help_text='comma seperated search strings like: ExceptionReport>, ServiceException>', max_length=256, verbose_name='Check response does not contain')),
                ('height', models.IntegerField(default=256)),
                ('width', models.IntegerField(default=256)),
                ('bbox_lat_lon', django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326, verbose_name='bounding box')),
                ('check_response_is_image', models.BooleanField(default=True)),
                ('format', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registry.mimetype')),
                ('layers', models.ManyToManyField(to='registry.layer')),
                ('reference_system', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='registry.referencesystem')),
                ('setting', models.ForeignKey(help_text='The related setting object', on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s', to='registry.webmapservicemonitoringsetting', verbose_name='Setting')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GetCapabilitiesProbe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timeout', models.IntegerField(blank=True, default=30)),
                ('check_response_does_not_contain', models.CharField(blank=True, default='ExceptionReport>, ServiceException>', help_text='comma seperated search strings like: ExceptionReport>, ServiceException>', max_length=256, verbose_name='Check response does not contain')),
                ('check_response_is_valid_xml', models.BooleanField(default=True)),
                ('check_response_does_contain', models.CharField(blank=True, default='Title>,Abstract>', help_text='comma seperated search strings like: Title>,Abstract>', max_length=256, verbose_name='Check response does contain')),
                ('setting', models.ForeignKey(help_text='The related setting object', on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s', to='registry.webmapservicemonitoringsetting', verbose_name='Setting')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='LayerGetFeatureInfoResult',
        ),
        migrations.DeleteModel(
            name='LayerGetMapResult',
        ),
        migrations.DeleteModel(
            name='WMSGetCapabilitiesResult',
        ),
    ]
