from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from api.models import Individual, Family

class PingTest(TestCase):

    def test_ping_endpoint(self):
        """
        Verify that we get a response when we ping the endpoint.
        """
        client = APIClient()
        response = client.get('/api/v1/ping/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('pong'), True)
