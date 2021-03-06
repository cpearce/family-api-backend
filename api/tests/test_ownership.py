from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from api.models import Individual, Family

class OwnershipTests(TestCase):

    def test_editors_group(self):
        # Verify that user can't edit entries if they're not in the 'editors' group.
        alice = User.objects.create_user('alice', password='test-password')
        self.assertEqual(alice.is_staff, False)
        self.assertEqual(alice.groups.count(), 0)

        # alice should not be able to create an individual, as she's not an eitor.
        client = APIClient()
        client.force_authenticate(user=alice)
        response = client.post('/api/v1/individuals/', {}, format='json')
        self.assertEqual(response.status_code, 403)

        # Create an Individual, alice should not be able to edit it.
        susan = Individual.objects.create(first_names='Susan')
        url = '/api/v1/individuals/{}/'.format(susan.id)
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 403)

        # Make alice staff; now she should be able to edit.
        alice.is_staff = True
        alice.save()
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 200)

        # Revoke staff, but make alice an editor.
        alice.is_staff = False
        editors_group = Group.objects.get(name='editors')
        alice.groups.add(editors_group)
        alice.save()

        # Alice can now create Individuals.
        response = client.post('/api/v1/individuals/', {}, format='json')
        self.assertEqual(response.status_code, 201)

        # But alice cannot edit the susan individual, as she's not the owner.
        response = client.patch(url, {'first_names': 'Susan Jane'}, format='json')
        self.assertEqual(response.status_code, 403)

        # Make alice the owner of the susan individual; now alice should be
        # able to edit susan.
        susan.owner = alice
        susan.save()
        response = client.patch(url, {'first_names': 'susan'}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_individual_ownership(self):
        editors_group = Group.objects.get(name='editors')
        alice = User.objects.create_user('alice', password='test-password')
        alice.groups.add(editors_group)
        bob = User.objects.create_user('bob',  password='test-password')
        bob.groups.add(editors_group)

        # Create individual owned by alice.
        client = APIClient()
        client.force_authenticate(user=alice)
        response = client.post('/api/v1/individuals/', {}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.get('owner'), 'alice')
        id = response.data.get('id')

        # Verify that alice is allowed to patch it.
        url = '/api/v1/individuals/{}/'.format(id)
        response = client.patch(url, {'first_names': 'tom'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('owner'), 'alice')
        self.assertEqual(response.data.get('first_names'), 'tom')

        # Verify that bob isn't allowed; he's not the owner.
        client.force_authenticate(user=bob)
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 403)

        # Staff should be allowed to change anything.
        staff = User.objects.create_user('staff',  password='test-password', is_staff=True)
        client.force_authenticate(user=staff)
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('last_name'), 'tester')

        # An individual with no owner should not be editable by a regular user...
        susan = Individual.objects.create(first_names='Susan')
        url = '/api/v1/individuals/{}/'.format(susan.id)
        client.force_authenticate(user=bob)
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 403)

        # ...but should be editable by staff.
        client.force_authenticate(user=staff)
        response = client.patch(url, {'last_name': 'tester'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('last_name'), 'tester')


    def test_family_ownership(self):
        editors_group = Group.objects.get(name='editors')
        alice = User.objects.create_user('alice', password='test-password')
        alice.groups.add(editors_group)
        bob = User.objects.create_user('bob',  password='test-password')
        bob.groups.add(editors_group)

        susan = Individual.objects.create(first_names='Susan')
        steve = Individual.objects.create(first_names='Steve')

        # Create family owned by alice.
        client = APIClient()
        client.force_authenticate(user=alice)
        response = client.post('/api/v1/families/', {'children':[], 'partners':[susan.id, steve.id]}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.get('owner'), 'alice')
        id = response.data.get('id')

        # Verify that alice is allowed to patch it.
        url = '/api/v1/families/{}/'.format(id)
        response = client.patch(url, {'married_location': 'gore'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('owner'), 'alice')
        self.assertEqual(response.data.get('married_location'), 'gore')

        # Verify that bob isn't allowed; he's not the owner.
        client.force_authenticate(user=bob)
        response = client.patch(url, {'married_location': 'matuara'}, format='json')
        self.assertEqual(response.status_code, 403)

        # Staff should be allowed to change anything.
        staff = User.objects.create_user('staff',  password='test-password', is_staff=True)
        client.force_authenticate(user=staff)
        response = client.patch(url, {'married_location': 'milton'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('married_location'), 'milton')

        # A family with no owner should not be editable by a regular user...
        family = Family.objects.create()
        url = '/api/v1/families/{}/'.format(family.id)
        client.force_authenticate(user=bob)
        response = client.patch(url, {'married_location': 'dunedin'}, format='json')
        self.assertEqual(response.status_code, 403)

        # ...but should be editable by staff.
        client.force_authenticate(user=staff)
        response = client.patch(url, {'married_location': 'dunedin'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('married_location'), 'dunedin')
