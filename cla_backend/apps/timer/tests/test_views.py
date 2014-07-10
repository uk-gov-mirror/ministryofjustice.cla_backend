from django.core.urlresolvers import reverse

from rest_framework import status

from core.tests.test_base import CLAAuthBaseApiTestMixin

from core.tests.mommy_utils import make_recipe

from timer.models import Timer


class TimerAPIMixin(CLAAuthBaseApiTestMixin):
    def setUp(self):
        super(TimerAPIMixin, self).setUp()

        self.detail_url = reverse(
            '%s:timer-detail' % self.API_URL_NAMESPACE
        )

    def test_methods_not_allowed(self):
        self._test_patch_not_allowed(self.detail_url)
        self._test_put_not_allowed(self.detail_url)
        self._test_delete_not_allowed(self.detail_url)

    def test_methods_not_authorized(self):
        self._test_get_not_authorized(self.detail_url, self.invalid_token)
        self._test_post_not_authorized(self.detail_url, self.invalid_token)

    def test_200_when_timer_is_running(self):
        timer = make_recipe('timer.Timer', created_by=self.user)

        response = self.client.post(
            self.detail_url, data={},
            format='json', HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], timer.created)

    def test_201_when_no_timer_is_running(self):
        self.assertEqual(Timer.objects.count(), 0)
        response = self.client.post(
            self.detail_url, data={},
            format='json', HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Timer.objects.count(), 1)

        timer = Timer.objects.all()[0]
        self.assertEqual(timer.created_by, self.user)

    def test_get_404_without_timers(self):
        response = self.client.get(
            self.detail_url,
            format='json', HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_200(self):
        timer = make_recipe('timer.Timer', created_by=self.user)

        response = self.client.get(
            self.detail_url,
            format='json', HTTP_AUTHORIZATION='Bearer %s' % self.token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(timer.created_by, self.user)
        self.assertEqual(timer.created, response.data['created'])
