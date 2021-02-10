from django.urls import path
from structure.views import *
from django.utils.translation import gettext as _

app_name = 'structure'
urlpatterns = [

    # PendingTask
    path('tasks/<pk>/remove', PendingTaskDelete.as_view(), name='remove-task'),
    path('report/error/<report_id>', generate_error_report, name='generate-error-report'),

    path('', index, name='index'),

    # MrMapGroup
    path('groups', MrMapGroupTableView.as_view(), name='groups-index'),
    path('groups/new', NewMrMapGroup.as_view(), name='new-group'),
    # path('groups/<pk>', MrMapGroupDetailView.as_view(), name='detail-group'),
    path('groups/<pk>', MrMapGroupDetailView.as_view(), name=_('group_detail')),

    path('groups/<pk>/members', MrMapGroupMembersTableView.as_view(), name='detail-group-members'),
    path('groups/<pk>/edit', EditGroupView.as_view(), name='edit-group'),
    path('groups/<pk>/remove', DeleteMrMapGroupView.as_view(), name='delete-group'),
    path('groups/<pk>/publishers', MrMapGroupPublishersTableView.as_view(), name='publisher-group'),
    path('groups/<pk>/publishers/new', MrMapGroupPublishersNewView.as_view(), name='group_publishers_new'),
    path('groups/<pk>/publishers/requests', MrMapGroupPublishRequestTableView.as_view(), name='group_publishers_requests'),


    path('groups/<object_id>/user/<user_id>', remove_user_from_group, name='remove-user-from-group'),

    path('publish-request/<object_id>/', toggle_publish_request, name='toggle-publish-request'),

    # Organization
    path('organizations/', organizations_index, name='organizations-index'),
    path('organizations/detail/<object_id>', detail_organizations, name='detail-organization'),
    path('organizations/edit/<object_id>', edit_org, name='edit-organization'),
    path('organizations/delete/<object_id>', remove_org, name='delete-organization'),
    path('organizations/create-publish-request/<org_id>/', publish_request, name='publish-request'),
    path('organizations/<org_id>/remove-publisher/<group_id>/', remove_publisher, name='remove-publisher'),
    path('organizations/new/register-form/', new_org, name='new-organization'),

    path('users/', users_index, name='users-index'),
    path('users/<object_id>/group-invitation/', user_group_invitation, name='invite-user-to-group'),

    path('group-invitation/<object_id>/', toggle_group_invitation, name='toggle-user-to-group'),
]

