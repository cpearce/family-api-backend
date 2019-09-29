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
        (id_str, id_str, datetime, str, List[id_str], str)
        which corresponds to:
        (husband, wife, date, place, children, note)
        """
        husband = ''
        wife = ''
        date = ''
        place = ''
        children = []
        note = ''
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
                    if marriage_data.get_tag() == 'NOTE':
                        note = marriage_data.get_value()
        return (husband, wife, date, place, children, note)

    def parse_indi(self, indi_element):
        (first, last) = indi_element.get_name()
        (birth_date, birth_place, _) = indi_element.get_birth_data()
        (death_date, death_place, _) = indi_element.get_death_data()
        (burial_date, burial_place, _) = indi_element.get_burial_data()

        note = ''
        bap_date = ''
        bap_place = ''
        for child in indi_element.get_child_elements():
            if child.get_tag() == 'NOTE':
                note += child.get_value()
                for grand_child in child.get_child_elements():
                    if grand_child.get_tag() == 'CONC':
                        note += grand_child.get_value()
                    else:
                        raise Exception('Can\'t handle tag {} in NOTE'.format(grand_child.get_tag()))
            if child.get_tag() == 'BAPM':
                for grand_child in child.get_child_elements():
                    if grand_child.get_tag() == 'DATE':
                        bap_date = grand_child.get_value()
                    elif grand_child.get_tag() == 'PLAC':
                        bap_place = grand_child.get_value()
                    else:
                        raise Exception('Can\'t handle tag {} in BAPM'.format(grand_child.get_tag()))

        return Individual(
            first_names = first,
            last_name = last,
            sex = indi_element.get_gender(),
            birth_date = to_date(birth_date),
            birth_location = birth_place,
            death_date = to_date(death_date),
            death_location = death_place,
            buried_date = to_date(burial_date),
            buried_location = burial_place,
            baptism_date = to_date(bap_date),
            baptism_location = bap_place,
            occupation = indi_element.get_occupation(),
            note = note,
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
                individuals[element.get_pointer()] = self.parse_indi(element)
            elif isinstance(element, FamilyElement):
                families.append(self.parse_family(element))

        # Note: in order to relations in the DB, we need to commit the
        # Individuals to the DB so they have valid PK's.
        for individual in individuals.values():
            individual.save()

        for (husband, wife, date, place, children, note) in families:
            family = Family(
                married_date = to_date(date),
                married_location = place,
                note = note,
            )
            family.save()
            for partner in filter(lambda k: k != '', [husband, wife]):
                individuals[partner].partner_in_families.add(family)
                individuals[partner].save()

            for child in children:
                if individuals[child].child_in_family != None:
                    raise Exception("Can't handle child {} being a child of two families!".format(child))
                individuals[child].child_in_family = family
                individuals[child].save()

        self.stdout.write(self.style.SUCCESS('Successfully parsed {} individuals {} families'.format(
            len(individuals), len(families))))
