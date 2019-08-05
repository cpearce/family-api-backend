from django.test import TestCase
from api.models import Individual
from io import StringIO
from django.core.management import call_command
from django.test import TestCase

class ImportGedcomTest(TestCase):
    def test_import(self):
        out = StringIO()
        call_command('importgedcom', 'api/tests/family.ged', stdout=out)
        self.assertIn('Successfully parsed', out.getvalue())

        father = Individual.objects.get(last_name = "FamilyName", first_names = "Father Figure")
        mother = Individual.objects.get(last_name = "MaidenName", first_names = "Mother Figure")
        grandfather = Individual.objects.get(last_name = "FamilyName", first_names = "Grandfather")
        grandma = Individual.objects.get(last_name = "GrandMaidenName", first_names = "Grandma")
        son1 = Individual.objects.get(last_name = "FamilyName", first_names = "Eldest son")
        son2 = Individual.objects.get(last_name = "FamilyName", first_names = "Middle Child")
        daughter = Individual.objects.get(last_name = "FamilyName", first_names = "Daughter")

        grand_parents = father.parents()
        self.assertEqual(len(grand_parents), 2)
        self.assertTrue(grandfather in grand_parents)
        self.assertTrue(grandma in grand_parents)

        fathers_spouses = father.spouses()
        self.assertEquals(len(fathers_spouses), 1)
        self.assertTrue(mother in fathers_spouses)

        mothers_spouses = mother.spouses()
        self.assertEquals(len(mothers_spouses), 1)
        self.assertTrue(father in mothers_spouses)

        fathers_children = father.children()
        self.assertEquals(len(fathers_children), 3)
        self.assertTrue(all(map(lambda c: c in fathers_children, [son1, son2, daughter])))

        mothers_children = mother.children()
        self.assertEquals(len(mothers_spouses), 1)
        self.assertTrue(all(map(lambda c: c in mothers_children, [son1, son2, daughter])))
