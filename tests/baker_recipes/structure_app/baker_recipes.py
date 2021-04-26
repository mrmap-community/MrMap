import os
<<<<<<< HEAD
=======
import random

from celery import states
>>>>>>> 6547e7f6ad710c8351a3ede267a054c17a44fa14
from django.contrib.auth.hashers import make_password
from django_celery_results.models import TaskResult
from model_bakery import seq
from model_bakery.recipe import Recipe, foreign_key, related
<<<<<<< HEAD
from structure.models import Organization, PendingTask, PublishRequest
from structure.models import MrMapUser
=======
from structure.models import Organization, PublishRequest, GroupInvitationRequest
from structure.models import MrMapUser, MrMapGroup
from structure.settings import SUPERUSER_GROUP_NAME, PUBLIC_GROUP_NAME
>>>>>>> 6547e7f6ad710c8351a3ede267a054c17a44fa14
from tests.test_data import get_password_data


salt = str(os.urandom(25).hex())
PASSWORD = get_password_data().get('valid')
EMAIL = "test@example.com"


god_user = Recipe(
    MrMapUser,
    username="God",
    email="god@heaven.va",
    salt=salt,
    password=make_password("354Dez25!"),
    is_active=True,
)

superadmin_orga = Recipe(
    Organization,
    name=seq("SuperOrganization"),
)


superadmin_user = Recipe(
    MrMapUser,
    username="Superuser",
    email="test@example.com",
    salt=salt,
    password=make_password(PASSWORD, salt=salt),
    is_active=True,
    #groups=related(superadmin_group),
    organization=foreign_key(superadmin_orga),
    is_superuser=True
)




active_testuser = Recipe(
    MrMapUser,
    username="Testuser",
    email="test@example.com",
    salt=salt,
    password=make_password(PASSWORD, salt=salt),
    is_active=True,
    groups=related(guest_group)
)

inactive_testuser = active_testuser.extend(
    is_active=False,
)

publish_request = Recipe(
    PublishRequest,
    group=foreign_key(superadmin_group),
    organization=foreign_key(non_autogenerated_orga),
)

group_invitation_request = Recipe(
    GroupInvitationRequest,
    to_group=foreign_key(superadmin_group),
    invited_user=foreign_key(active_testuser),
    message="Test",
)

pending_task = Recipe(
    TaskResult,
    status=states.STARTED,
    task_id=1
)
