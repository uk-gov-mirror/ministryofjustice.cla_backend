import mock

from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from cla_common.constants import REQUIRES_ACTION_BY

from legalaid.tests.views.test_base import CLAProviderAuthBaseApiTestMixin

from legalaid.tests.views.mixins.case_api import FullCaseAPIMixin, \
    BaseSearchCaseAPIMixin, BaseUpdateCaseTestCase

from cla_eventlog.tests.test_views import ExplicitEventCodeViewTestCaseMixin, \
    ImplicitEventCodeViewTestCaseMixin

from cla_provider.serializers import CaseSerializer
from cla_provider.forms import RejectCaseForm


class BaseCaseTestCase(
    CLAProviderAuthBaseApiTestMixin, FullCaseAPIMixin, APITestCase
):

    @property
    def response_keys(self):
        return [
            'eligibility_check', 'personal_details', 'reference',
            'created', 'modified', 'created_by',
            'provider', 'notes', 'provider_notes',
            'full_name', 'laa_reference', 'eligibility_state',
            'adaptation_details', 'requires_action_by',
            'matter_type1', 'matter_type2', 'diagnosis', 'media_code',
            'postcode', 'diagnosis_state', 'thirdparty_details',
            'exempt_user', 'exempt_user_reason',
            'language', 'thirdparty_full_name', 'ecf_statement'
        ]

    def get_extra_search_make_recipe_kwargs(self):
        return {
            'provider': self.provider,
            'requires_action_by': REQUIRES_ACTION_BY.PROVIDER
        }

    def get_case_serializer_clazz(self):
        return CaseSerializer

    def make_resource(self):
        return super(BaseCaseTestCase, self).make_resource(
            provider=self.provider,
            requires_action_by=REQUIRES_ACTION_BY.PROVIDER
        )


class CaseGeneralTestCase(BaseCaseTestCase):
    def test_methods_not_allowed(self):
        """
        Ensure that we can't POST, PUT or DELETE
        """
        ### LIST
        self._test_delete_not_allowed(self.list_url)
        self._test_post_not_allowed(self.list_url)

        # ### DETAIL
        self._test_delete_not_allowed(self.detail_url)


class SearchCaseTestCase(BaseSearchCaseAPIMixin, BaseCaseTestCase):
    pass


class UpdateCaseTestCase(BaseUpdateCaseTestCase, BaseCaseTestCase):
    def test_patch_provider_notes_allowed(self):
        """
        Test that provider can post provider notes
        """
        response = self.client.patch(
            self.detail_url, data={'provider_notes': 'abc123'},
            format='json', HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['provider_notes'], 'abc123')

    def test_patch_operator_notes_not_allowed(self):
        """
        Test that provider cannot post operator notes
        """
        response = self.client.patch(
            self.detail_url, data={'notes': 'abc123'},
            format='json', HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['notes'], 'abc123')


class RejectCaseTestCase(ExplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    def get_event_code(self):
        form = RejectCaseForm(case=mock.MagicMock())
        return form.fields['event_code'].choices[0][0]

    def get_url(self, reference=None):
        reference = reference or self.resource.reference
        return reverse(
            'cla_provider:case-reject', args=(),
            kwargs={'reference': reference}
        )


class AcceptCaseTestCase(ImplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    NO_BODY_RESPONSE = False

    def get_url(self, reference=None):
        reference = reference or self.resource.reference
        return reverse(
            'cla_provider:case-accept', args=(),
            kwargs={'reference': reference}
        )


class CloseCaseTestCase(ImplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    def get_url(self, reference=None):
        reference = reference or self.resource.reference
        return reverse(
            'cla_provider:case-close', args=(),
            kwargs={'reference': reference}
        )
