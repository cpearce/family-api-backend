import json

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.models import PasswordResetRequest
from api.permissions import in_editors_group

def add_to_editors_group(user):
    editors_group = Group.objects.get(name='editors')
    user.groups.add(editors_group)
    user.save()

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

    def test_account_set_password(self):
        client = APIClient()

        # Create user to create another user from.
        alice = User.objects.create_user('alice', password='test-password',
            first_name='alice', last_name='alexander', email='alice@example.com')
        # Log in alice, to get her auth token.
        response = client.post('/api/v1/login/', data={
            'username': 'alice',
            'password': 'test-password',
        })
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Token ' + response.data.get('token'))

        # Create an account for bob.
        response = client.post('/api/v1/create-account/', data={
            'username': 'bob',
            'email': 'bob@example.com',
            'first_name': 'bob',
            'last_name': 'test',
            'send_confirmation_email': False,
        })
        self.assertEqual(response.status_code, 201)

        # Find the new user created.
        bob = User.objects.filter(username='bob').first()
        self.assertIsNotNone(bob)
        # Since bob was created by the 'create-account' endpoint, he should
        # be an editor.
        self.assertTrue(in_editors_group(bob))
        pw_reset_request = PasswordResetRequest.objects.filter(user=bob).first()
        self.assertIsNotNone(pw_reset_request)

        # Verify that the new user can't login.
        client.credentials() # wipe credentials.
        response = client.post('/api/v1/login/', data={
            'username': 'bob',
            'password': '',
        })
        self.assertEqual(response.status_code, 400)

        # We are un-auth'd, reset should work logged out.
        response = client.post('/api/v1/reset-password/', data={
            'token': pw_reset_request.token,
            'password': 'another-test-password',
            'send_confirmation_email': False,
        })
        self.assertEqual(response.status_code, 200)

        # Log in.
        response = client.post('/api/v1/login/', data={
            'username': 'bob',
            'password': 'another-test-password',
        })
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Token ' + response.data.get('token'))

        # Verify that bob can make requests.
        response = client.get('/api/v1/search-individuals/bob')
        self.assertEqual(response.status_code, 200)

    def test_recover_password(self):
        client = APIClient()

        # Spam a password reset for an email without an account.
        # Should be a no-op.
        pw_reset_count = PasswordResetRequest.objects.count()
        response = client.post('/api/v1/recover-account/', data={
            'email': 'bob@example.com',
            'send_confirmation_email': False,
        })
        self.assertEqual(response.status_code, 200) # It's always 200.
        # Should not have created any new objects.
        self.assertEqual(PasswordResetRequest.objects.count(), pw_reset_count)

        # Create user to clear password.
        alice = User.objects.create_user('alice', password='test-password',
            first_name='alice', last_name='alexander', email='alice@example.com')

        response = client.post('/api/v1/recover-account/', data={
            'email': 'alice@example.com',
            'send_confirmation_email': False,
        })
        # It's always 200.
        self.assertEqual(response.status_code, 200)

        # Alice wasn't an editor, so the PW reset should have failed silently.
        pw_reset_request = PasswordResetRequest.objects.filter(user=alice).first()
        self.assertIsNone(pw_reset_request)

        # Make alice an editor, and try again.
        add_to_editors_group(alice)
        response = client.post('/api/v1/recover-account/', data={
            'email': 'alice@example.com',
            'send_confirmation_email': False,
        })
        # It's always 200.
        self.assertEqual(response.status_code, 200)

        # Should now have a PW reset request, since alice is editable.
        pw_reset_request = PasswordResetRequest.objects.filter(user=alice).first()
        self.assertIsNotNone(pw_reset_request)

        response = client.post('/api/v1/reset-password/', data={
            'token': pw_reset_request.token,
            'password': 'another-test-password',
            'send_confirmation_email': False,
        })
        self.assertEqual(response.status_code, 200)

        # Log in.
        response = client.post('/api/v1/login/', data={
            'username': 'alice',
            'password': 'another-test-password',
        })
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Token ' + response.data.get('token'))

        # Verify that alice can make requests.
        response = client.get('/api/v1/search-individuals/alice')
        self.assertEqual(response.status_code, 200)
