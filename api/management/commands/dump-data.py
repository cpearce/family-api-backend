from django.core.management.base import BaseCommand, CommandError
from api.models import Individual, Family

import json


def serialize_individual(individual):
    return {
        "first_names": str_or_none(individual.first_names),
        "last_name": str_or_none(individual.last_name),
        "sex": str_or_none(individual.sex),
        "birth": {
            "date": str_or_none(individual.birth_date),
            "location": str_or_none(individual.birth_location),
        },
        "death": {
            "date": str_or_none(individual.death_location),
            "location": str_or_none(individual.death_location),
        },
        "buried": {
            "date": str_or_none(individual.buried_date),
            "location": str_or_none(individual.buried_location),
        },
        "baptism": {
            "date": str_or_none(individual.baptism_date),
            "location": str_or_none(individual.baptism_location),
        },
        "occupation": str_or_none(individual.occupation),
        "child_in_family": str(individual.child_in_family.id)
        if individual.child_in_family
        else None,
        "note": str_or_none(individual.note),
        "spouse_in_family": [str(f.id) for f in individual.partner_in_families.all()],
    }


def str_or_none(value):
    return str(value) if value else None


def serialize_family(f):
    return {
        "married": {
            "date": str_or_none(f.married_date),
            "location": str_or_none(f.married_location),
        }
    }


def dump_data(output_file_path):
    individuals = {
        i.id: serialize_individual(i)
        for i in Individual.objects.prefetch_related("partner_in_families").all()
    }
    families = {f.id: serialize_family(f) for f in Family.objects.all()}

    data = {"individuals": individuals, "families": families}

    with open(output_file_path, "w") as f:
        f.write(json.dumps(data, indent=2))


class Command(BaseCommand):
    help = "Exports database in JSON format"

    def add_arguments(self, parser):
        parser.add_argument("output_file_path")

    def handle(self, *args, **options):
        output_file_path = options["output_file_path"]
        dump_data(output_file_path)
