from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus

class DashboardViewTests(TestCase):
    def test_test_view(self):
        response = self.client.get(reverse('dashboard:test'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content.decode(), "Dashboard app is working!") 