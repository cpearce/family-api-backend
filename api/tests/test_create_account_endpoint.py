import json

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
# from api.models import Individual, Family

class CreateAccountEndpointTest(TestCase):

    def test_missing_fields(self):
        client = APIClient()
        response = client.post('/api/v1/create-account/')
        # Not logged in.
        self.assertEqual(response.status_code, 401)

        # Create a user without edit access.
        alice = User.objects.create_user('alice', password='test-password',
            first_name='alice', last_name='alexander', email='alice@example.com')
        # Assert alice doesn't have editor or staff status.
        self.assertEqual(alice.is_staff, False)
        self.assertEqual(alice.groups.count(), 0)

        # Post create-account with all fields missing, verify that fields
        # were rejected.
        client.force_authenticate(user=alice)
        response = client.post('/api/v1/create-account/')
        self.assertEqual(response.status_code, 400)
        expected = {
            "Missing field 'username'": False,
            "Missing field 'email'": False,
            "Missing field 'first_name'": False,
            "Missing field 'last_name'": False,
        }
        for error in response.data.get('errors'):
            self.assertIn(error, expected)
            # Shouldn't get duplicate errors.
            self.assertFalse(expected[error])
            expected[error] = True
        for _, found in expected.items():
            self.assertTrue(found)
