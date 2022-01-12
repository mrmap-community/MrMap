# Generated by Django 3.2.9 on 2022-01-12 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0006_auto_20220112_1848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mapcontextlayer',
            name='name',
        ),
        migrations.AlterField(
            model_name='mapcontextlayer',
            name='title',
            field=models.CharField(help_text='an identifying name for this map context layer', max_length=1000, verbose_name='title'),
        ),
    ]
