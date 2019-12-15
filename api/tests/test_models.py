from django.test import TestCase
from django.utils import timezone
from api.models import Individual, Family, FamilyNameList, search_terms
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

class SearchTermTest(TestCase):
    def test_search_terms(self):
        self.assertSetEqual({"okeefe", "tylerlee"}, set(search_terms("O'Keefe & Tyler-Lee")))

class FamilyNameListTest(TestCase):
    def create_family(self, wife_first_name, wife_last_name, husband_first_name, husband_last_name):
        husband = Individual.objects.create(first_names=husband_first_name, last_name=husband_last_name, sex="M")
        wife = Individual.objects.create(first_names=wife_first_name, last_name=wife_last_name, sex="F")
        family = Family.objects.create()
        family.partners.add(wife)
        family.partners.add(husband)
        family.save()
        return husband, wife, family

    def test_search(self):
        bob, alice, alice_and_bob = self.create_family("Alice", "Aitken", "Bob", "Baker")
        ben, audrey, audrey_and_ben = self.create_family("Audrey", "Hepburn", "Ben", "Franklin")

        bob_and_audrey = Family.objects.create()
        bob_and_audrey.partners.add(bob)
        bob_and_audrey.save()
        bob_and_audrey.partners.add(audrey)
        bob_and_audrey.save()

        families = set(FamilyNameList.search("Alice Aitken & Bob Baker"))
        self.assertSetEqual({alice_and_bob}, families)

        families = set(FamilyNameList.search("Bob Baker"))
        self.assertSetEqual({alice_and_bob, bob_and_audrey}, families)
