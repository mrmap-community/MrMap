"""
Author: Michel Peltriaux
Organization: Spatial data infrastructure Rhineland-Palatinate, Germany
Contact: michel.peltriaux@vermkv.rlp.de
Created on: 22.04.20

"""
from django.test import TestCase, RequestFactory

from MrMap.consts import STRUCTURE_INDEX_GROUP, STRUCTURE_INDEX_ORGANIZATION
from structure.filters import GroupFilter, OrganizationFilter
from structure.models import MrMapGroup, Organization
from structure.tables import GroupTable, OrganizationTable
from tests import utils
from tests.baker_recipes.db_setup import create_guest_groups, create_superadminuser, \
    create_public_organization, create_random_named_orgas, create_non_autogenerated_orgas
from tests.baker_recipes.structure_app.baker_recipes import PASSWORD


class StructureTablesTestCase(TestCase):

    def setUp(self):
        # creates user object in db
        self.user_password = PASSWORD
        self.groups = create_guest_groups(how_much_groups=9)
        self.user = create_superadminuser(groups=self.groups)
        self.orgas = create_non_autogenerated_orgas(
            user=self.user,
            how_much_orgas=10
        )
        # Set individual organization for each group
        i = 0
        for group in self.groups:
            group.organization = self.orgas[i]
            group.save()
            i = i+1

        # Public group needs an organization for this test
        public_orga = create_public_organization(
            user=self.user,
        )[0]
        public_group = MrMapGroup.objects.get(is_public_group=True)
        public_group.organization = public_orga
        public_group.save()

        self.user.organization = self.orgas[0]
        self.user.save()
        self.user.refresh_from_db()

        self.request_factory = RequestFactory()
        # Create an instance of a GET request.
        self.request = self.request_factory.get('/')
        # Recall that middleware are not supported. You can simulate a
        # logged-in user by setting request.user manually.
        self.request.user = self.user

        self.groups_url_path_name = STRUCTURE_INDEX_GROUP
        self.orgs_url_path_name = STRUCTURE_INDEX_ORGANIZATION

    def test_group_table_sorting(self):
        """ Run test to check the sorting functionality of the group tables

        Return:

        """
        # Get all groups, make sure the initial set is ordered by random
        groups = MrMapGroup.objects.all().order_by("?")
        sorting_param = "sg"
        table = GroupTable(
            data=groups,
            order_by_field=sorting_param,
            request=self.request
        )
        # Check table sorting
        sorting_implementation_failed, sorting_results = utils.check_table_sorting(
            table=table,
            url_path_name=self.groups_url_path_name,
            sorting_parameter=sorting_param
        )

        for key, val in sorting_results.items():
            self.assertTrue(val, msg="Group table sorting not correct for column '{}'".format(key))
        for key, val in sorting_implementation_failed.items():
            self.assertFalse(val, msg="Group table sorting leads to error for column '{}'".format(key))

    def test_group_table_filtering(self):
        """ Run test to check the filtering functionality of the group tables

        Return:

        """
        groups = MrMapGroup.objects.all()
        filter_param = "gsearch"
        sorting_param = "sg"
        table = GroupTable(
            data=groups,
            order_by_field=sorting_param,
            request=self.request
        )

        filter_results = utils.check_table_filtering(
            table=table,
            filter_parameter=filter_param,
            queryset=groups,
            filter_class=GroupFilter,
            table_class=GroupTable,
            user=self.user,
        )

        for key, val in filter_results.items():
            self.assertTrue(val, msg="Group table filtering not correct for column '{}'".format(key))

    def test_organization_table_sorting(self):
        """ Run test to check the sorting functionality of the group tables

        Return:

        """
        # Get all groups, make sure the initial set is ordered by random
        orgs = Organization.objects.all().order_by("?")
        sorting_param = "so"
        table = OrganizationTable(
            data=orgs,
            order_by_field=sorting_param,
            request=self.request
        )
        # Check table sorting
        sorting_implementation_failed, sorting_results = utils.check_table_sorting(
            table=table,
            url_path_name=self.orgs_url_path_name,
            sorting_parameter=sorting_param
        )

        for key, val in sorting_results.items():
            self.assertTrue(val, msg="Organization table sorting not correct for column '{}'".format(key))
        for key, val in sorting_implementation_failed.items():
            self.assertFalse(val, msg="Organization table sorting leads to error for column '{}'".format(key))

    def test_organization_table_filtering(self):
        """ Run test to check the filtering functionality of the group tables

        Return:

        """
        orgs = Organization.objects.all()
        filter_param = "osearch"
        sorting_param = "so"
        table = OrganizationTable(
            data=orgs,
            order_by_field=sorting_param,
            request=self.request
        )

        filter_results = utils.check_table_filtering(
            table=table,
            filter_parameter=filter_param,
            queryset=orgs,
            filter_class=OrganizationFilter,
            table_class=OrganizationTable,
            user=self.user,
        )

        for key, val in filter_results.items():
            self.assertTrue(val, msg="Organization table filtering not correct for column '{}'".format(key))

