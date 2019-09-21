from django.core.management.base import BaseCommand, CommandError
from api.models import Individual, Family


class Command(BaseCommand):
    help = 'Updates all pre-computed family names stored in DB'

    def handle(self, *args, **options):
        self.run()

    def run(self):
        for family in Family.objects.all():
            family.save()
            self.stdout.write(family.name)
