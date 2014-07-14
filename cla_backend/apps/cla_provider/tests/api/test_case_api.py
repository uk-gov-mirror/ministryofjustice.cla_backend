import mock
from datetime import datetime

from django.core.urlresolvers import reverse
from django.utils.timezone import utc

from rest_framework import status
from rest_framework.test import APITestCase

from core.tests.mommy_utils import make_recipe
from core.tests.test_base import CLAProviderAuthBaseApiTestMixin

from cla_eventlog.tests.test_views import ImplicitEventCodeViewTestCaseMixin, \
    ExplicitEventCodeViewTestCaseMixin

from legalaid.models import Case
from cla_common.constants import REQUIRES_ACTION_BY

from cla_provider.forms import RejectCaseForm


class BaseCaseTestCase(CLAProviderAuthBaseApiTestMixin, APITestCase):
    def setUp(self):
        super(BaseCaseTestCase, self).setUp()

        self.list_url = reverse('cla_provider:case-list')
        obj = make_recipe(
            'legalaid.case', provider=self.provider,
            requires_action_by=REQUIRES_ACTION_BY.PROVIDER
        )
        self.check = obj
        self.detail_url = reverse(
            'cla_provider:case-detail', args=(),
            kwargs={'reference': obj.reference}
        )

    def assertCaseCheckResponseKeys(self, response):
        self.assertItemsEqual(
            response.data.keys(),
            ['eligibility_check', 'personal_details', 'reference',
             'created', 'modified', 'created_by', 'log_set',
             'provider', 'locked_by', 'locked_at', 'notes', 'provider_notes',
             'laa_reference', 'requires_action_by']
        )

    def assertPersonalDetailsEqual(self, data, obj):
        if data is None or obj is None:
            self.assertEqual(data, obj)
        else:
            for prop in ['title', 'full_name', 'postcode', 'street', 'mobile_phone', 'home_phone']:
                self.assertEqual(unicode(getattr(obj, prop)), data[prop])

    def assertCaseEqual(self, data, case):
        self.assertEqual(case.reference, data['reference'])
        self.assertEqual(unicode(case.eligibility_check.reference), data['eligibility_check'])
        self.assertPersonalDetailsEqual(data['personal_details'], case.personal_details)


class CaseViewTestCase(BaseCaseTestCase):
    def test_methods_not_allowed(self):
        """
        Ensure that we can't POST, PUT or DELETE
        """
        ### LIST
        self._test_delete_not_allowed(self.list_url)

        ### DETAIL
        self._test_delete_not_allowed(self.detail_url)

        ### CREATE
        self._test_post_not_allowed(self.list_url)

    def test_methods_not_authorized_operator_key(self):
        """
        Ensure that we can't POST, PUT or DELETE using operator
        token
        """
        ### LIST
        self._test_delete_not_authorized(self.list_url, self.operator_token)

        ### DETAIL
        self._test_delete_not_authorized(self.detail_url, self.operator_token)

        ### CREATE
        self._test_post_not_authorized(self.list_url, self.operator_token)

    def test_list_allowed(self):
        """
        GET list-url should work
        """
        Case.objects.all().delete()

        provider2 = make_recipe('cla_provider.Provider')

        # this should appear in the list
        obj1 = make_recipe(
            'legalaid.case', provider=self.provider,
            requires_action_by=REQUIRES_ACTION_BY.PROVIDER
        )
        # this shouldn't because requires_action_by is not PROVIDER
        make_recipe(
            'legalaid.case', provider=self.provider,
            requires_action_by=None
        )
        # this shouldn't appear because belonging to another provider
        make_recipe(
            'legalaid.case', provider=provider2,
            requires_action_by=REQUIRES_ACTION_BY.PROVIDER
        )
        # this shouldn't appear because requires_action_by == OPERATOR
        make_recipe(
            'legalaid.case', provider=self.provider,
            requires_action_by=REQUIRES_ACTION_BY.OPERATOR
        )

        # this should appear in the list
        obj2 = make_recipe(
            'legalaid.case', provider=self.provider,
            requires_action_by=REQUIRES_ACTION_BY.PROVIDER_REVIEW
        )

        response = self.client.get(
            self.list_url, data={}, format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.data))
        self.assertCaseEqual(response.data[0], obj2)  # cases in review first
        self.assertCaseEqual(response.data[1], obj1)

    def test_get_allowed(self):
        response = self.client.get(
            self.detail_url, data={}, format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCaseCheckResponseKeys(response)
        self.assertCaseEqual(response.data, self.check)

    def test_locked_by_when_getting_case(self):

        self.assertEqual(self.check.locked_by, None)
        self.assertEqual(self.check.locked_at, None)
        response = self.client.get(
            self.detail_url, data={}, format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['locked_by'], 'john')

        # check the time was set by this test
        self.assertFalse(response.data['locked_at'] == None)
        time_diff = datetime.utcnow().replace(tzinfo=utc)-response.data['locked_at']
        self.assertTrue(time_diff.seconds<3)

    # SEARCH

    def test_search_find_one_result_by_name(self):
        """
        GET search by name should work
        """

        obj = make_recipe('legalaid.case',
                          reference='ref1',
                          personal_details__full_name='xyz',
                          personal_details__postcode='123',
                          requires_action_by=REQUIRES_ACTION_BY.PROVIDER,
                          provider=self.provider,
                          )

        self.check.personal_details.full_name = 'abc'
        self.check.personal_details.postcode = '123'
        self.check.personal_details.save()
        self.check.reference = 'ref2'
        self.check.save()

        response = self.client.get(
            self.list_url, data={'search':'abc'}, format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertCaseEqual(response.data[0], self.check)

    def test_search_find_one_result_by_ref(self):
        """
        GET search by ref should work
        """

        obj = make_recipe('legalaid.case', provider=self.provider,
                          personal_details__full_name='abc',
                          personal_details__postcode='123')


        response = self.client.get(
            self.list_url, data={'search':self.check.reference}, format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertCaseEqual(response.data[0], self.check)

    def test_search_find_one_result_by_postcode(self):
        """
        GET search by name should work
        """

        obj = make_recipe('legalaid.case', provider=self.provider,
                          personal_details__postcode='123',
                          personal__details__full_name='abc')

        response = self.client.get(
            self.list_url, data={'search': self.check.personal_details.postcode},
            format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(response.data))
        self.assertCaseEqual(response.data[0], self.check)

    def test_search_find_none_result_by_postcode(self):
        """
        GET search by name should work
        """

        response = self.client.get(
            self.list_url, data={'search': self.check.personal_details.postcode+'ss'},
            format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data))


    def test_search_find_none_result_by_fullname(self):
        """
        GET search by name should work
        """
        response = self.client.get(
            self.list_url, data={'search': self.check.personal_details.full_name+'ss'},
            format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data))


    def test_search_find_none_result_by_ref(self):
        """
        GET search by name should work
        """
        response = self.client.get(
            self.list_url, data={'search': self.check.reference+'ss'},
            format='json',
            HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.data))

    def test_patch_provider_notes_allowed(self):
        """
        Test that provider can post provider notes
        """
        response = self.client.patch(self.detail_url, data={'provider_notes': 'abc123'},
                                     format='json', HTTP_AUTHORIZATION='Bearer %s' % self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['provider_notes'], 'abc123')


class RejectCaseTestCase(ExplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    def get_event_code(self):
        form = RejectCaseForm(case=mock.MagicMock())
        return form.fields['event_code'].choices[0][0]

    def get_url(self, reference=None):
        reference = reference or self.check.reference
        return reverse(
            'cla_provider:case-reject', args=(),
            kwargs={'reference': reference}
        )


class AcceptCaseTestCase(ImplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    def get_url(self, reference=None):
        reference = reference or self.check.reference
        return reverse(
            'cla_provider:case-accept', args=(),
            kwargs={'reference': reference}
        )


class CloseCaseTestCase(ImplicitEventCodeViewTestCaseMixin, BaseCaseTestCase):
    def get_url(self, reference=None):
        reference = reference or self.check.reference
        return reverse(
            'cla_provider:case-close', args=(),
            kwargs={'reference': reference}
        )
