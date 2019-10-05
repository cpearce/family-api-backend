import datetime

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from api.models import Individual, Family

class AccountEndpointTests(TestCase):

    def test_account_endpoint(self):
        # Verify that user can't edit entries if they're not in the 'editors' group.
        alice = User.objects.create_user('alice', password='test-password')
        self.assertEqual(alice.is_staff, False)
        self.assertEqual(alice.groups.count(), 0)

        # Verify that new users have no privileges.
        client = APIClient()
        client.force_authenticate(user=alice)
        response = client.get('/api/v1/account/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['is_staff'], False)
        self.assertEqual(response.data['is_editor'], False)

        # Verify that making staff is reflected.
        alice.is_staff = True
        alice.save()
        response = client.get('/api/v1/account/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['is_staff'], True)
        self.assertEqual(response.data['is_editor'], False)

        # Verify that making editor is reflected.
        alice.is_staff = False
        editors_group = Group.objects.get(name='editors')
        alice.groups.add(editors_group)
        alice.save()
        response = client.get('/api/v1/account/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['is_staff'], False)
        self.assertEqual(response.data['is_editor'], True)

        # Verify that user can be both togegher.
        alice.is_staff = True
        alice.save()
        response = client.get('/api/v1/account/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')
        self.assertEqual(response.data['is_staff'], True)
        self.assertEqual(response.data['is_editor'], True)
