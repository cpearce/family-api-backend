from django.core.management.base import BaseCommand, CommandError
from api.models import Individual, Family

from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
import dateparser
import gedcom
from collections import defaultdict

def to_date(s):
    if s == "":
        return None
    #  Note: dateparser uses local time zone by default.
    return dateparser.parse(s, settings={'RETURN_AS_TIMEZONE_AWARE': True})

class Command(BaseCommand):
    help = 'Imports database in GEDCOM format'

    def add_arguments(self, parser):
        parser.add_argument('gedcom_file_path')

    def handle(self, *args, **options):
        self.import_gedcom_file(options['gedcom_file_path'])

    def parse_family(self, family_element):
        """
        Parses a GEDCOM family tag, returns a list of:
        (id_str, id_str, datetime, str, List[id_str])
        which corresponds to:
        (husband, wife, date, place, children)
        """
        husband = ''
        wife = ''
        date = ''
        place = ''
        children = []
        for element in family_element.get_child_elements():
            if element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND:
                husband = element.get_value()
            elif element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE:
                wife = element.get_value()
            elif element.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD:
                children.append(element.get_value())
            elif element.get_tag() == gedcom.tags.GEDCOM_TAG_MARRIAGE:
                for marriage_data in element.get_child_elements():
                    if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = marriage_data.get_value()
                    if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = marriage_data.get_value()
        return (husband, wife, date, place, children)

    def parse_indi(self, element):
        (first, last) = element.get_name()
        (birth_date, birth_place, _) = element.get_birth_data()
        (death_date, death_place, _) = element.get_death_data()
        (burial_date, burial_place, _) = element.get_burial_data()
        return Individual(
            first_names = first,
            last_name = last,
            sex = element.get_gender(),
            birth_date = to_date(birth_date),
            birth_location = birth_place,
            death_date = to_date(death_date),
            death_location = death_place,
            buried_date = to_date(burial_date),
            buried_location = burial_place,
            occupation = element.get_occupation(),
        )

    def import_gedcom_file(self, gedcom_file_path):
        gedcom_parser = Parser()
        gedcom_parser.parse_file(gedcom_file_path)
        root_child_elements = gedcom_parser.get_root_child_elements()

        # Parse all elements in the GEDCOM file, recording details from
        # individual and family elements.

        families = []
        # Lookup from gedcom individual pointer (e.g. "@I219") to api.Individual.
        individuals = dict()
        for element in root_child_elements:
            if isinstance(element, IndividualElement):
                individuals[element.get_pointer()] = self.parse_indi(element);
            elif isinstance(element, FamilyElement):
                families.append(self.parse_family(element))

        # Note: in order to relations in the DB, we need to commit the
        # Individuals to the DB so they have valid PK's.
        for id, individual in individuals.items():
            individual.save()

        for (husband, wife, date, place, children) in families:
            family = Family(
                married_date = to_date(date),
                married_location = place,
            )
            family.save()
            for partner in filter(lambda k: k != '', [husband, wife]):
                individuals[partner].partner_in_families.add(family)
                individuals[partner].save()

            for child in children:
                individuals[child].child_in_family = family
                individuals[child].save()

        self.stdout.write(self.style.SUCCESS('Successfully parsed {} individuals {} families'.format(
            len(individuals), len(families))))
