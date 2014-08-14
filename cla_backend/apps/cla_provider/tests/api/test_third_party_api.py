from rest_framework.test import APITestCase
from rest_framework import status

from core.tests.test_base import CLAProviderAuthBaseApiTestMixin
from core.tests.mommy_utils import make_recipe

from cla_common.constants import REQUIRES_ACTION_BY

from legalaid.tests.views.mixins.third_party_api import \
    ThirdPartyDetailsApiMixin


class ThirdPartyDetailsTestCase(
    CLAProviderAuthBaseApiTestMixin, ThirdPartyDetailsApiMixin, APITestCase
):

    def setUp(self):
        super(ThirdPartyDetailsTestCase, self).setUp()

        self.check_case.provider = self.provider
        self.check_case.requires_action_by = REQUIRES_ACTION_BY.PROVIDER
        self.check_case.save()

    def get_http_authorization(self):
        return 'Bearer %s' % self.staff_token

    # SECURITY

    def test_get_not_found_if_not_belonging_to_provider(self):
        self.check_case.provider = None
        self.check_case.requires_action_by = REQUIRES_ACTION_BY.OPERATOR
        self.check_case.save()

        response = self.client.get(
            self.detail_url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_not_found_if_belonging_to_different_provider(self):
        other_provider = make_recipe('cla_provider.provider')

        self.check_case.provider = other_provider
        self.check_case.save()

        response = self.client.get(
            self.detail_url, format='json',
            HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)