import datetime

from django.test import TestCase
from django.utils import timezone
from api.models import Individual, Family
from django.urls import reverse

class IndividualModelTests(TestCase):
    def test_create(self):
        alice = Individual(first_names="Alice", last_name="Aitken", sex="F")
        bob = Individual(first_names="Bob", last_name="Baker", sex="M")

        alice.save()
        bob.save()

        self.assertIs(len(Individual.objects.all()), 2);

        grandad = Individual(first_names="Grandad", last_name="Foo", sex="M")
        grandad.save()

        grandma = Individual(first_names="Grandma", last_name="Bar", sex="F")
        grandma.save()
        self.assertIs(len(Individual.objects.all()), 4);

        family = Family()
        family.save()
        family.partners.add(grandad)
        family.partners.add(grandma)

        for child in [alice, bob]:
            child.child_in_family = family
            child.save()

        for parent in [grandad, grandma]:
            self.assertIs(len(parent.partner_in_families.all()), 1)
