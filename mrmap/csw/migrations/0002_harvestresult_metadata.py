# Generated by Django 3.1.8 on 2021-05-03 06:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('service', '0001_initial'),
        ('csw', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='harvestresult',
            name='metadata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='harvest_results', to='service.metadata'),
        ),
    ]
