# Generated by Django 3.1.8 on 2021-04-26 09:46

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConformityCheckConfiguration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1000)),
                ('metadata_types', models.JSONField()),
                ('conformity_type', models.TextField(choices=[('internal', 'internal'), ('etf', 'etf')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1000)),
                ('field_name', models.TextField(choices=[('title', 'title'), ('abstract', 'abstract'), ('access_constraints', 'access_constraints'), ('keywords', 'keywords'), ('formats', 'formats'), ('reference_system', 'reference_system')])),
                ('property', models.TextField(choices=[('len', 'len'), ('count', 'count')])),
                ('operator', models.TextField(choices=[('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<='), ('==', '=='), ('!=', '!=')])),
                ('threshold', models.TextField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConformityCheckConfigurationExternal',
            fields=[
                ('conformitycheckconfiguration_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='quality.conformitycheckconfiguration')),
                ('external_url', models.URLField(max_length=1000, null=True)),
                ('validation_target', models.TextField(max_length=1000, null=True)),
                ('parameter_map', models.JSONField()),
                ('polling_interval_seconds', models.IntegerField(blank=True, default=5)),
                ('polling_interval_seconds_max', models.IntegerField(blank=True, default=300)),
            ],
            options={
                'abstract': False,
            },
            bases=('quality.conformitycheckconfiguration',),
        ),
        migrations.CreateModel(
            name='ConformityCheckConfigurationInternal',
            fields=[
                ('conformitycheckconfiguration_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='quality.conformitycheckconfiguration')),
            ],
            options={
                'abstract': False,
            },
            bases=('quality.conformitycheckconfiguration',),
        ),
        migrations.CreateModel(
            name='RuleSet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1000)),
                ('rules', models.ManyToManyField(related_name='rule_set', to='quality.Rule')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConformityCheckRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time_start', models.DateTimeField(auto_now_add=True)),
                ('time_stop', models.DateTimeField(blank=True, null=True)),
                ('passed', models.BooleanField(blank=True, null=True)),
                ('result', models.TextField(blank=True, null=True)),
                ('conformity_check_configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quality.conformitycheckconfiguration')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
