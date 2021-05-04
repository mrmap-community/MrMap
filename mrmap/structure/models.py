import uuid

import six
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, When
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_bootstrap_swt.components import LinkButton, Tag, Badge
from django_bootstrap_swt.enums import ButtonColorEnum, BadgeColorEnum, TooltipPlacementEnum, ButtonSizeEnum
from MrMap.icons import IconEnum, get_icon
from MrMap.messages import REQUEST_ACTIVATION_TIMEOVER
from service.helper.crypto_handler import CryptoHandler
from service.helper.enums import OGCServiceEnum, MetadataEnum
from structure.permissionEnums import PermissionEnum
from structure.settings import USER_ACTIVATION_TIME_WINDOW
from users.settings import default_activation_time, default_request_activation_time


class Contact(models.Model):
    person_name = models.CharField(max_length=200, default="", null=True, blank=True, verbose_name=_("Contact person"))
    email = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_('E-Mail'))
    phone = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_('Phone'))
    facsimile = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("Facsimile"))
    city = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("City"))
    postal_code = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("Postal code"))
    address_type = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("Address type"))
    address = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("Address"))
    state_or_province = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("State or province"))
    country = models.CharField(max_length=100, default="", null=True, blank=True, verbose_name=_("Country"))

    def __str__(self):
        return self.person_name

    class Meta:
        abstract = True


class Organization(Contact):
    organization_name = models.CharField(max_length=255, null=True, default="", verbose_name=_('Organization name'))
    description = models.TextField(default="",
                                   null=True,
                                   blank=True,
                                   verbose_name=_('description'),)
    parent = models.ForeignKey('self',
                               on_delete=models.DO_NOTHING,
                               blank=True,
                               null=True,
                               verbose_name=_('Parent organization'),
                               help_text=_('Configure a inheritance structure for this Organization'))
    is_auto_generated = models.BooleanField(default=True,
                                            verbose_name=_('autogenerated'),
                                            help_text=_('Autogenerated organizations are resolved from registered resources.'))
    created_by = models.ForeignKey('MrMapUser',
                                   related_name='created_by',
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization_name",
                    "person_name",
                    "email",
                    "phone",
                    "facsimile",
                    "city",
                    "postal_code",
                    "address_type",
                    "address",
                    "state_or_province",
                    "country",
                    "description",
                ],
                name="unique organizations"
            )
        ]
        # define default ordering for this model. This is needed for django tables2 ordering. If we use just the
        # foreignkey as column accessor the ordering will be done by the primary key. To avoid this we need to define
        # the right default way here...
        ordering = ['organization_name']

        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        permissions = [
            ("remove_publisher", "Can remove publisher")
        ]

    @property
    def icon(self):
        return get_icon(IconEnum.ORGANIZATION)

    def __str__(self):
        if self.organization_name is None:
            return ""
        return self.organization_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.check_circular_configuration(self)
        super().save(force_insert, force_update, using, update_fields)

    @classmethod
    def check_circular_configuration(cls, instance):
        if instance.parent is not None:
            if instance == instance.parent:
                raise ValidationError(_("Circular configuration of parent organization detected."))
            else:
                _parent = instance.parent.parent
                while _parent is not None:
                    if instance == _parent:
                        raise ValidationError(_("Circular configuration of parent organization detected."))
                    else:
                        _parent = _parent.parent

    def get_absolute_url(self):
        return self.detail_view_uri

    @property
    def members_view_uri(self):
        return reverse('structure:organization_members', args=[self.pk, ])

    @property
    def publishers_uri(self):
        return reverse('structure:organization_publisher_overview', args=[self.pk, ])

    @classmethod
    def get_add_action(cls):
        icon = Tag(tag='i', attrs={"class": [IconEnum.ADD.value]}).render()
        st_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=icon).render()
        gt_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                      content=icon + _(' new organization').__str__()).render()
        return LinkButton(content=st_text + gt_text,
                          color=ButtonColorEnum.SUCCESS,
                          url=reverse('structure:organization_new'),
                          needs_perm=PermissionEnum.CAN_EDIT_GROUP.value)

    @property
    def detail_view_uri(self):
        return reverse('structure:organization_details', args=[self.pk, ])

    @property
    def add_view_uri(self):
        return reverse('structure:organization_new', args=[self.pk, ])

    @property
    def edit_view_uri(self):
        return reverse('structure:organization_edit', args=[self.pk, ])

    @property
    def remove_view_uri(self):
        return reverse('structure:organization_remove', args=[self.pk, ])

    def get_actions(self):
        add_icon = Tag(tag='i', attrs={"class": [IconEnum.ADD.value]}).render()
        st_pub_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=add_icon).render()
        gt_pub_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                          content=add_icon + _(' become publisher').__str__()).render()
        edit_icon = Tag(tag='i', attrs={"class": [IconEnum.EDIT.value]}).render()
        st_edit_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=edit_icon).render()
        gt_edit_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                           content=edit_icon + _(' edit').__str__()).render()
        actions = [
            LinkButton(url=f"{reverse('structure:publish_request_new',)}?organization={self.id}",
                       content=st_pub_text + gt_pub_text,
                       color=ButtonColorEnum.SUCCESS,
                       size=ButtonSizeEnum.SMALL,
                       tooltip=format_html(
                           _(f"Become publisher for organization <strong>{self.organization_name} [{self.id}]</strong>")),
                       tooltip_placement=TooltipPlacementEnum.LEFT,
                       needs_perm=PermissionEnum.CAN_REQUEST_TO_BECOME_PUBLISHER.value),
            LinkButton(url=self.edit_view_uri,
                       content=st_edit_text + gt_edit_text,
                       color=ButtonColorEnum.WARNING,
                       size=ButtonSizeEnum.SMALL,
                       tooltip=format_html(_(f"Edit <strong>{self.organization_name} [{self.id}]</strong> organization")),
                       tooltip_placement=TooltipPlacementEnum.LEFT,
                       needs_perm=PermissionEnum.CAN_EDIT_ORGANIZATION.value),
        ]

        if not self.is_auto_generated:
            remove_icon = Tag(tag='i', attrs={"class": [IconEnum.DELETE.value]}).render()
            st_remove_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=remove_icon).render()
            gt_remove_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                                 content=remove_icon + _(' remove').__str__()).render()
            actions.append(LinkButton(url=self.remove_view_uri,
                                      content=st_remove_text + gt_remove_text,
                                      color=ButtonColorEnum.DANGER,
                                      size=ButtonSizeEnum.SMALL,
                                      tooltip=format_html(_(f"Remove <strong>{self.organization_name} [{self.id}]</strong> organization")),
                                      tooltip_placement=TooltipPlacementEnum.LEFT,
                                      needs_perm=PermissionEnum.CAN_DELETE_ORGANIZATION.value))
        return actions


class MrMapGroup(Group):
    description = models.TextField(blank=True, verbose_name=_('Description'))
    parent_group = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True,
                                     related_name="children_groups")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="organization_groups")
    publish_for_organizations = models.ManyToManyField('Organization', related_name='publishers', blank=True)
    created_by = models.ForeignKey('MrMapUser', on_delete=models.DO_NOTHING)
    is_public_group = models.BooleanField(default=False)
    is_permission_group = models.BooleanField(default=False)

    class Meta:
        ordering = [Case(When(name='Public', then=0)), 'name']
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        permissions = [
            ("add_user_to_group", "Can add user to a group"),
            ("remove_user_from_group", "Can remove user from a group"),
            ("request_to_become_publisher", "Can request to become publisher"),
        ]

    @property
    def icon(self):
        return get_icon(IconEnum.GROUP)

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        is_new = False
        if self._state.adding:
            is_new = True
            if not self.created_by:
                raise ValidationError(_('you must define created_by to save new instances'))

        super().save(force_insert, force_update, using, update_fields)
        if is_new:
            self.user_set.add(self.created_by)

    def delete(self, using=None, keep_parents=False, force=False):
        if (self.is_permission_group or self.is_public_group) and not force:
            raise ValidationError(_("Group {} is an important main group and therefore can not be removed.").format(_(self.name)))
        return super().delete(using=using, keep_parents=keep_parents)

    def get_absolute_url(self):
        return reverse('structure:group_details', args=[self.pk, ])

    @classmethod
    def get_add_view_url(self):
        return reverse('structure:group_new')

    @classmethod
    def get_add_action(cls):
        return LinkButton(content=get_icon(IconEnum.ADD) + _(' New group').__str__(),
                          color=ButtonColorEnum.SUCCESS,
                          url=reverse('structure:group_new'),
                          needs_perm=PermissionEnum.CAN_EDIT_GROUP.value)

    @property
    def detail_view_uri(self):
        return reverse('structure:group_details', args=[self.pk, ])

    @property
    def add_view_uri(self):
        return reverse('structure:group_new')

    @property
    def edit_view_uri(self):
        return reverse('structure:group_edit', args=[self.pk, ])

    @property
    def remove_view_uri(self):
        return reverse('structure:group_remove', args=[self.pk, ])

    @property
    def members_view_uri(self):
        return reverse('structure:group_members', args=[self.pk, ])

    @property
    def publish_rights_for_uri(self):
        return reverse('structure:group_publish_rights_overview', args=[self.pk, ])

    @property
    def new_publisher_requesst_uri(self):
        return f"{reverse('structure:publish_request_new')}?group={self.pk}"

    @property
    def icon(self):
        return get_icon(IconEnum.GROUP)

    def get_actions(self, request: HttpRequest):
        actions = []
        if not self.is_permission_group:
            edit_icon = Tag(tag='i', attrs={"class": [IconEnum.EDIT.value]}).render()
            st_edit_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=edit_icon).render()
            gt_edit_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']}, content=edit_icon + _(' Edit').__str__()).render()
            actions.append(LinkButton(url=self.edit_view_uri,
                                      content=st_edit_text + gt_edit_text,
                                      color=ButtonColorEnum.WARNING,
                                      tooltip=_(f"Edit <strong>{self.name}</strong>"),
                                      needs_perm=PermissionEnum.CAN_EDIT_GROUP.value))
            delete_icon = Tag(tag='i', attrs={"class": [IconEnum.DELETE.value]}).render()
            st_delete_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=delete_icon).render()
            gt_delete_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']}, content=delete_icon + _(' Delete').__str__()).render()
            actions.append(LinkButton(url=self.remove_view_uri,
                                      content=st_delete_text + gt_delete_text,
                                      color=ButtonColorEnum.DANGER,
                                      tooltip=_(f"Remove <strong>{self.name}</strong>"),
                                      needs_perm=PermissionEnum.CAN_DELETE_GROUP.value))

            if request.user not in self.user_set.all():
                add_user_icon = Tag(tag='i', attrs={"class": [IconEnum.USER_ADD.value]}).render()
                st_add_user_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=add_user_icon).render()
                gt_add_user_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                                       content=delete_icon + _(' become member').__str__()).render()
                actions.append(LinkButton(url=f"{reverse('structure:group_invitation_request_new')}?group={self.pk}&user={request.user.id}",
                                          content=st_add_user_text + gt_add_user_text,
                                          color=ButtonColorEnum.SUCCESS,
                                          tooltip=_(f"Become member of  <strong>{self.name}</strong>")))
            elif self.user_set.count() > 1:
                from MrMap.utils import signal_last
                groups_querystring = "groups"
                groups_excluded_self = request.user.groups.exclude(pk=self.pk)
                if groups_excluded_self:
                    groups_querystring = ""
                    for is_last_element, group in signal_last(groups_excluded_self):
                        if is_last_element:
                            groups_querystring += f"groups={group.pk}"
                        else:
                            groups_querystring += f"groups={group.pk}&"

                leave_icon = Tag(tag='i', attrs={"class": [IconEnum.USER_REMOVE.value]}).render()
                st_leave_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=leave_icon).render()
                gt_leave_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                                    content=delete_icon + _(' leave group').__str__()).render()
                actions.append(LinkButton(
                    url=f"{reverse('edit_profile')}?{groups_querystring}",
                    content=st_leave_text + gt_leave_text,
                    color=ButtonColorEnum.SUCCESS,
                    tooltip=_(f"Become member of  <strong>{self.name}</strong>")))
        return actions

    @property
    def new_publisher_request_action(self):
        add_icon = Tag(tag='i', attrs={"class": [IconEnum.ADD.value]}).render()
        st_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=add_icon).render()
        gt_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']}, content=add_icon + _(' become publisher').__str__()).render()
        return LinkButton(url=self.new_publisher_requesst_uri,
                          content=st_text + gt_text,
                          color=ButtonColorEnum.SUCCESS,
                          tooltip=_("Become rights to publish"),
                          needs_perm=PermissionEnum.CAN_REQUEST_TO_BECOME_PUBLISHER.value)

    @property
    def show_pending_requests(self):
        icon = Tag(tag='i', attrs={"class": [IconEnum.PUBLISHERS.value]}).render()
        count = Badge(content=f" {PublishRequest.objects.filter(group=self).count()}", color=BadgeColorEnum.SECONDARY).render()
        st_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=icon + count).render()
        gt_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                      content=icon + _(' pending requests').__str__() + count).render()
        return LinkButton(url=f"{reverse('structure:publish_request_overview')}?group={self.pk}",
                          content=f"{st_text}{gt_text}",
                          color=ButtonColorEnum.INFO,
                          tooltip=_(f"see pending requests for {self}"),
                          needs_perm=PermissionEnum.CAN_REQUEST_TO_BECOME_PUBLISHER.value)


class MrMapUser(AbstractUser):
    salt = models.CharField(max_length=500)
    organization = models.ForeignKey('Organization', related_name='primary_users', on_delete=models.SET_NULL, null=True,
                                     blank=True)
    confirmed_newsletter = models.BooleanField(default=False, verbose_name=_("I want to sign up for the newsletter"))
    confirmed_survey = models.BooleanField(default=False, verbose_name=_("I want to participate in surveys"))
    confirmed_dsgvo = models.DateTimeField(auto_now_add=True,
                                           verbose_name=_("I understand and accept that my data will be automatically processed and securely stored, as it is stated in the general data protection regulation (GDPR)."))

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    @property
    def icon(self):
        return get_icon(IconEnum.USER)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('password_change_done')

    def get_edit_view_url(self):
        return reverse('edit_profile')

    @property
    def invite_to_group_url(self):
        return f"{reverse('structure:group_invitation_request_new')}?user={self.id}"

    def get_services(self, type: OGCServiceEnum = None):
        """ Returns all services which are related to the user

        Returns:
             md_list (list): A list containing all services related to the user
        """
        return list(self.get_services_as_qs(type))

    def get_services_as_qs(self, type: OGCServiceEnum = None):
        """ Returns all services which are related to the user

        Returns:
             md_list:
        """
        from service.models import Metadata
        md_list = Metadata.objects.filter(
            service__is_root=True,
            created_by__in=self.groups.all(),
            service__is_deleted=False,
        ).order_by("title")
        if type is not None:
            md_list = md_list.filter(service__service_type__name=type.name.lower())
        return md_list

    def get_metadatas_as_qs(self, type: MetadataEnum = None, inverse_match: bool = False):
        """ Returns all metadatas which are related to the user

        Returns:
             md_list:
        """
        from service.models import Metadata

        md_list = Metadata.objects.filter(
            created_by__in=self.groups.all(),
        ).order_by("title")
        if type is not None:
            if inverse_match:
                md_list = md_list.all().exclude(metadata_type=type.name.lower())
            else:
                md_list = md_list.filter(metadata_type=type.name.lower())
        return md_list

    def get_datasets_as_qs(self, user_groups=None, count=False):
        """ Returns all datasets which are related to the user

        Returns:
             md_list:
        """
        from service.models import Metadata
        if user_groups is None:
            user_groups = self.groups.all()

        if count:
            md_list = Metadata.objects.filter(
                metadata_type=MetadataEnum.DATASET.value,
                created_by__in=user_groups,
            ).count()
        else:
            md_list = Metadata.objects.filter(
                metadata_type=MetadataEnum.DATASET.value,
                created_by__in=user_groups,
            ).order_by("title")
        return md_list

    def create_activation(self):
        """ Create an activation object

        Returns:
             nothing
        """
        # user does not exist yet! We need to create an activation object
        user_activation = UserActivation()
        user_activation.user = self
        user_activation.activation_until = timezone.now() + timezone.timedelta(hours=USER_ACTIVATION_TIME_WINDOW)
        sec_handler = CryptoHandler()
        user_activation.activation_hash = sec_handler.sha256(
            self.username + self.salt + str(user_activation.activation_until))
        user_activation.save()


class UserActivation(models.Model, PasswordResetTokenGenerator):
    user = models.OneToOneField(MrMapUser, null=False, blank=False, on_delete=models.CASCADE)
    activation_until = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=default_activation_time))
    activation_hash = models.CharField(primary_key=True, max_length=500)

    def __str__(self):
        return self.user.username

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self._state.adding:
            self.activation_hash = self.make_token(self.user)
        super().save(force_insert, force_update, using, update_fields)

    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) +
                six.text_type(user.email)
        )


class GroupActivity(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(MrMapUser, on_delete=models.CASCADE, blank=True, null=True)
    metadata = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description


class BaseInternalRequest(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    message = models.TextField(null=True, blank=True)
    activation_until = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=default_request_activation_time))
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self._state.adding:
            if timezone.now() > self.activation_until:
                self.delete()
                raise ValidationError(REQUEST_ACTIVATION_TIMEOVER)
        super().save(force_insert, force_update, using, update_fields)


class PublishRequest(BaseInternalRequest):
    group = models.ForeignKey(MrMapGroup, verbose_name=_('group'), related_name="pending_publish_requests", on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, verbose_name=_('organization'), related_name="pending_publish_requests", on_delete=models.CASCADE)
    is_accepted = models.BooleanField(verbose_name=_('accepted'), default=False)

    class Meta:
        # It shall be restricted to create multiple requests objects for the same organization per group. This unique
        # constraint will also raise a form error if a user trays to add duplicates.
        unique_together = ('group', 'organization',)
        verbose_name = _('Pending publish request')
        verbose_name_plural = _('Pending publish requests')
        permissions = [
            ("toggle_publish_requests", "Can toggle publish requests"),
        ]

    @property
    def icon(self):
        return get_icon(IconEnum.PUBLISHERS)

    def __str__(self):
        return "{} > {}".format(self.group.name, self.organization.organization_name)

    def get_absolute_url(self):
        return f"{reverse('structure:publish_request_overview')}?group={self.group.id}&organization={self.organization.id}"

    def get_accept_view_url(self):
        return reverse('structure:publish_request_accept', args=[self.pk])

    @classmethod
    def get_add_action(cls):
        icon = Tag(tag='i', attrs={"class": [IconEnum.ADD.value]}).render()
        st_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=icon).render()
        gt_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                      content=icon + _(' new publisher request').__str__()).render()
        return LinkButton(content=st_text + gt_text,
                          color=ButtonColorEnum.SUCCESS,
                          url=reverse('structure:publish_request_new'),
                          needs_perm=PermissionEnum.CAN_REQUEST_TO_BECOME_PUBLISHER.value)

    @property
    def accept_request_uri(self):
        return reverse('structure:publish_request_accept', args=[self.pk])

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        if not self._state.adding:
            if self.is_accepted:
                self.group.publish_for_organizations.add(self.organization)
                self.delete()


class GroupInvitationRequest(BaseInternalRequest):
    user = models.ForeignKey(MrMapUser, on_delete=models.CASCADE, related_name="pending_group_invitations", verbose_name=_('Invited user'), help_text=_('Invite this user to a selected group.'))
    group = models.ForeignKey(MrMapGroup, on_delete=models.CASCADE, verbose_name=_('to group'), help_text=_('Invite the selected user to this group.'), related_name='pending_group_invitations')
    is_accepted = models.BooleanField(verbose_name=_('accepted'), default=False)

    class Meta:
        # It shall be restricted to create multiple requests objects for the same user per group. This unique
        # constraint will also raise a form error if a user trays to add duplicates.
        unique_together = ('group', 'user',)
        verbose_name = _('Pending group invitation')
        verbose_name_plural = _('Pending group invitations')

    @property
    def icon(self):
        return get_icon(IconEnum.PUBLISHERS)

    def __str__(self):
        return "{} > {}".format(self.invited_user.username, self.to_group)

    @classmethod
    def get_add_action(cls):
        icon = Tag(tag='i', attrs={"class": [IconEnum.ADD.value]}).render()
        st_text = Tag(tag='div', attrs={"class": ['d-lg-none']}, content=icon).render()
        gt_text = Tag(tag='div', attrs={"class": ['d-none', 'd-lg-block']},
                      content=icon + _(' new group invitation').__str__()).render()
        return LinkButton(content=st_text + gt_text,
                          color=ButtonColorEnum.SUCCESS,
                          url=reverse('structure:group_invitation_request_new'),
                          needs_perm=PermissionEnum.CAN_ADD_USER_TO_GROUP.value)

    def get_absolute_url(self):
        return f"{reverse('structure:group_invitation_request_overview')}?group={self.group.id}&user={self.user.id}"

    @property
    def accept_request_uri(self):
        return reverse('structure:group_invitation_request_accept', args=[self.pk])

    @property
    def icon(self):
        return get_icon(IconEnum.PUBLISHERS)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self._state.adding:
            if self.is_accepted:
                self.group.user_set.add(self.user)
            self.delete()
        else:
            super().save(force_insert, force_update, using, update_fields)
