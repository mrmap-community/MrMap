"""
Core models to implement the possibility of Roles

For more information on this file, see
# todo: link to the docs

"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from guardian_roles.models.template_code import EDIT_LINK_BUTTON
from structure.models import Organization


class TemplateRole(models.Model):
    """`TemplateRole` model to handle of one or more permissions as a template.
    Use this model to construct your custom roles.
    """
    verbose_name = models.CharField(max_length=58,
                                    verbose_name=_("Verbose name"),
                                    help_text=_("The verbose name of the role"))
    description = models.TextField(verbose_name=_("Description"),
                                   help_text=_("Describe what permissions this role shall grant"))
    permissions = models.ManyToManyField(to=Permission, related_name='role_set')

    def __str__(self) -> str:
        return str(self.verbose_name)


class ConcreteTemplateRole(Group):
    # do not change after generation of this instance, cause permission changing is not implemented for base_template
    # changing.
    based_template = models.ForeignKey(to=TemplateRole, on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_("Description"),
                                   help_text=_("Describe what permissions this role shall grant"))

    class Meta:
        abstract = True

    def __str__(self):
        return '{} | {} | {}'.format(
            str(self.content_object),
            str(self.name),
            str([perm.codename for perm in self.based_template.permissions.all()]))

    def save(self, *args, **kwargs):
        adding = self._state.adding
        if adding:
            self.name = f'{self.content_object} | {self.based_template.verbose_name}'
            self.description = _('handle permissions based on the "').__str__() + self.based_template.__str__() + _(
                '" `TemplateRole` for "').__str__() + self.content_object.__str__() + '"'
        super().save(*args, **kwargs)


class OrganizationBasedTemplateRole(ConcreteTemplateRole):
    """OrganizationBasedTemplateRole model to handle Role groups per organization.

    Creation:
        On `Organization` creation, one `OrganizationBasedTemplateRole` per selected `TemplateRole` is generated.
        Handled by `CreateOrganizationWizard.done()`.

    Needed cause:
        This is necessary to configure which users of an `Organization` should basically have which role to manage
        objects of this organization. This makes it possible to treat users from different `Organization` have
        permissions to **all** objects of the specified `Organization`.

    User membership:
        Is handled by the user it self.
    """
    content_object = models.ForeignKey(to=Organization, on_delete=models.CASCADE,
                                       related_name='organization_based_template_roles')

    def get_absolute_url(self):
        return reverse('guardian_roles:organization_role_detail', args=[self.pk])

    def get_edit_url(self):
        return reverse('guardian_roles:organization_role_edit', args=[self.pk])

    def get_members_view_uri(self):
        return reverse('guardian_roles:organization_role_detail_members', args=[self.pk])

    def get_actions(self):
        return [format_html(EDIT_LINK_BUTTON % {'url': self.get_edit_url()})]


class ObjectBasedTemplateRole(ConcreteTemplateRole):
    """ObjectBasedTemplateRole model to handle Role groups per object.

    Creation:
        On object creation, one `ObjectBasedTemplateRole` per defined `Role` is generated.
        NOTE !!: do not create or change instance of this model manual.
          This `Permission` `Group`s are generated by permission/signals.py

    Needed cause:
        This is necessary to configure which users, independent of `Organization` membership, have permissions to a
        **specific** object.

    User membership:
        Is handled by `OrganizationBasedTemplateRole` objects. If a user is added/removed to a
        `OrganizationBasedTemplateRole` all users of this specific `OrganizationBasedTemplateRole` will be added/removed
         to all `ObjectBasedTemplateRole` objects with the same related base_template filtered by objects of the given
        `Organization`.
    """
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = GenericForeignKey(fk_field='object_pk')
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
