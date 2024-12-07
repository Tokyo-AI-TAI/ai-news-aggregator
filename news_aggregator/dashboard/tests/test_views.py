from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    def test_test_view(self):
        response = self.client.get(reverse("dashboard:test"))
        assert response.status_code == HTTPStatus.OK
        assert response.content.decode() == "Dashboard app is working!"
