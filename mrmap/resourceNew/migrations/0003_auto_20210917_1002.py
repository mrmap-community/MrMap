# Generated by Django 3.2.7 on 2021-09-17 08:02

from django.db import migrations, models
import resourceNew.models.document


class Migration(migrations.Migration):

    dependencies = [
        ('resourceNew', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetmetadata',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='featuretype',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='featuretypemetadata',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='layer',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='layermetadata',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='service',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
        migrations.AlterField(
            model_name='servicemetadata',
            name='xml_backup_file',
            field=models.FileField(editable=False, help_text='the original xml as backup to restore the xml field.', upload_to=resourceNew.models.document.xml_backup_file_path, verbose_name='xml backup'),
        ),
    ]
