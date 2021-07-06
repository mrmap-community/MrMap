# Generated by Django 3.2.4 on 2021-07-06 16:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('structure', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('service', '0001_initial'),
        ('acl', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='metadatauserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='metadatagroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service.metadata'),
        ),
        migrations.AddField(
            model_name='metadatagroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AddField(
            model_name='metadatagroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='accessible_accesscontrollists',
            field=models.ManyToManyField(blank=True, help_text="Select which acl's shall be accessible with the configured permissions.", related_name='_acl_accesscontrollist_accessible_accesscontrollists_+', to='acl.AccessControlList', verbose_name='Accessible access control lists'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='accessible_metadata',
            field=models.ManyToManyField(blank=True, help_text='Select which resource shall be accessible with the configured permissions.', to='service.Metadata', verbose_name='Accessible resource'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='accessible_organizations',
            field=models.ManyToManyField(blank=True, help_text='Select which organizations shall be accessible with the configured permissions.', to='structure.Organization', verbose_name='Accessible organizations'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='created_by_user',
            field=models.ForeignKey(blank=True, editable=False, help_text='The user who has created this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acl_accesscontrollist_created_by_user', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, editable=False, help_text='The last user who has modified this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acl_accesscontrollist_last_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Last modified by'),
        ),
        migrations.AddField(
            model_name='accesscontrollist',
            name='owned_by_org',
            field=models.ForeignKey(blank=True, editable=False, help_text='The organization which is the owner of this object.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acl_accesscontrollist_owned_by_org', to='structure.organization', verbose_name='Owner'),
        ),
        migrations.AlterUniqueTogether(
            name='metadatauserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='metadatagroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
    ]
