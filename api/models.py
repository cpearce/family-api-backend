from django.db import models
from datetime import date

# def _birth_date_or_min_year(individual):
#     """
#     Returns an individual's birth date, or if that's unknown,
#     the minimum representable date.
#     """
#     if individual.birth_date:
#         return individual.birth_date
#     return date.min

# def _married_date_or_min_year(partnership):
#     """
#     Returns a partnership's married date, or if that's unknown,
#     the minimum representable date.
#     """
#     if partnership.married_date:
#         return partnership.married_date
#     return date.min

class Individual(models.Model):
    first_names = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    SEX_CHOICES = [("M", "Male"), ("F", "Female"), ("?", "Unknown")]

    # TODO: This shouldn't be required; the sex of a child in the distant past
    # may be unknown.
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)

    birth_date = models.DateField('birth date', null=True, blank=True)
    birth_location = models.CharField(max_length=100, blank=True)

    death_date = models.DateField('death date', null=True, blank=True)
    death_location = models.CharField(max_length=100, blank=True)

    buried_date = models.DateField('buried date', null=True, blank=True)
    buried_location = models.CharField(max_length=100, blank=True)

    occupation = models.CharField(max_length=100, blank=True)

    child_in_family = models.ForeignKey(
        "Family", on_delete=models.CASCADE, related_name="children", null=True, blank=True)

    def reversed_str(self):
        s = self.last_name
        if len(s) > 0:
            s += ", "
        s += self.first_names
        l = self.lifetime()
        if len(l) > 0:
            if len(s) > 0:
                s += " "
            s += l
        return s

    def full_name(self):
        return " ".join([self.first_names, self.last_name])

    def __str__(self):
        return " ".join([self.full_name(), self.lifetime()])

    def lifetime(self):
        if self.birth_date is None and self.death_date is None:
            return ""
        s = "("
        if self.birth_date is not None:
            s += str(self.birth_date.year)
        else:
            s += "?"
        s += "-"
        if self.death_date is not None:
            s += str(self.death_date.year)
        else:
            s += "?"
        s += ")"
        return s

    def parents(self):
        # The partners of the family which this individual was a child in.
        if not self.child_in_family:
            return []
        return [
            p for p in self.child_in_family.partners.all()
        ]

    def children(self):
        # For each family in which this individual is a partner...
        # Append the individuals which are chilren in this family...
        return [
            i for family in self.partner_in_families.all()
                for i in Individual.objects.filter(
                    child_in_family=family
                )
        ]

    def spouses(self):
        return [
            p for family in self.partner_in_families.all()
                for p in family.partners.all()
                    if p != self
        ]

class Family(models.Model):
    married_date = models.DateField('married date', null=True, blank=True)
    married_location = models.CharField(max_length=100, blank=True)

    partners = models.ManyToManyField(
        Individual, related_name="partner_in_families", symmetrical=False)
