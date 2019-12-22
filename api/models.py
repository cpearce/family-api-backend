from django.db import models
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from collections import Counter
from functools import reduce

import re

import pytz

import string
import random

def fuzzy_date_year(value):
    digit_matches = re.findall(r"(\d+)", value)
    if not digit_matches:
        return None
    for s in filter(lambda x: len(x) == 4, digit_matches):
        return int(s)
    return None

def birth_date_or_min_year(individual):
    """
    Returns an individual's birth date, or if that's unknown, 0.
    """
    year = fuzzy_date_year(individual.birth_date)
    if year:
        return year
    return 0

def married_date_or_min_year(partnership):
    """
    Returns a partnership's married date, or if that's unknown, 0.
    """
    year = fuzzy_date_year(partnership.married_date)
    if year:
        return year
    return 0

class Individual(models.Model):
    first_names = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    SEX_CHOICES = [("M", "Male"), ("F", "Female"), ("?", "Unknown")]

    # TODO: This shouldn't be required; the sex of a child in the distant past
    # may be unknown.
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, blank=True)

    birth_date = models.CharField('birth date', max_length=50, blank=True)
    birth_location = models.CharField(max_length=100, blank=True)

    death_date = models.CharField('death date', max_length=50, blank=True)
    death_location = models.CharField(max_length=100, blank=True)

    buried_date = models.CharField('buried date', max_length=50, blank=True)
    buried_location = models.CharField(max_length=100, blank=True)

    baptism_date = models.CharField('baptism date', max_length=50, blank=True)
    baptism_location = models.CharField(max_length=100, blank=True)

    occupation = models.CharField(max_length=100, blank=True)

    child_in_family = models.ForeignKey(
        "Family", on_delete=models.CASCADE, related_name="children", null=True, blank=True)

    note = models.TextField(blank=True, null=True)

    owner = models.ForeignKey('auth.User', related_name='individuals', null=True, on_delete=models.SET_NULL)

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

    # firstnames lastname
    def full_name(self):
        return " ".join(filter(None, [self.first_names, self.last_name]))

    # lastname, firstnames
    def formal_name(self):
        return ", ".join(filter(None, [self.last_name, self.first_names]))

    def __str__(self):
        # Return $name + $lifetime.
        # Note: the filter(None...) filters out empty strings, so we don't end up
        # joining " " with "" and getting an extra space in the full name.
        return " ".join(filter(None, [self.formal_name(), self.lifetime()]))

    def lifetime(self):
        if not self.birth_date and not self.death_date:
            return ""
        s = "("
        if self.birth_date:
            s += str(fuzzy_date_year(self.birth_date))
        else:
            s += "?"
        s += "-"
        if self.death_date:
            s += str(fuzzy_date_year(self.death_date))
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
        return sorted([
            i for family in self.partner_in_families.all()
                for i in Individual.objects.filter(
                    child_in_family=family
                )
        ], key=birth_date_or_min_year)

    def spouses(self):
        return [
            p for family in self.partner_in_families.all()
                for p in family.partners.all()
                    if p != self
        ]

    def save(self, *args, **kwargs):
        # Update names of family's, in case this person's name
        # changed, which changes the family name.
        super(Individual, self).save(*args, **kwargs)
        for family in self.partner_in_families.all():
            family.update_family_name()


class Family(models.Model):
    married_date = models.CharField('married date', max_length=50, blank=True)
    married_location = models.CharField(max_length=100, blank=True)

    partners = models.ManyToManyField(
        Individual, related_name="partner_in_families", symmetrical=False)

    # Computed field; the name of the partners in the field.
    # Stored in DB to make retrieval cheap.
    name = models.CharField(max_length=210, blank=True)

    note = models.TextField(blank=True, null=True)

    owner = models.ForeignKey('auth.User', related_name='families', null=True, on_delete=models.SET_NULL)

    def update_family_name(self):
        # Sort list first by last name, second by sex with males first.
        partners_list = list(self.partners.all());
        partners_list.sort(key=lambda i: i.last_name)
        partners_list.sort(key=lambda i: i.sex, reverse=True)
        partners_list = map(str, partners_list)
        self.name = " & ".join(partners_list)
        # Note: Don't pass args/kwargs here, else we'll try to re-create a new
        # instance, which will fail!
        super().save()
        FamilyNameList.ensure_indexed(self)

    def save(self, *args, **kwargs):
        if not self.id:
            # We need to have a valid ID before calling the `partners()` function
            # below, so double save here. This hits when creating new instances.
            super(Family, self).save(*args, **kwargs)
        self.update_family_name()

def random_token(N):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=N))

class PasswordResetRequest(models.Model):
    user = models.ForeignKey('auth.User', related_name='password_reset_token', null=True, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, db_index=True)
    expires = models.DateTimeField()

    @classmethod
    def create(cls, user):
        utc_now = pytz.utc.localize(datetime.utcnow())
        return PasswordResetRequest.objects.create(
            user=user,
            token=random_token(50),
            expires=utc_now+timedelta(days=3)
        )

    @classmethod
    def find(cls, token):
        utc_now = pytz.utc.localize(datetime.utcnow())
        reset_requests = list(PasswordResetRequest.objects.filter(token=token))
        result = None
        for reset_request in reset_requests:
            if reset_request.expires < utc_now:
                reset_request.delete()
            else:
                result = reset_request

        return result

def search_terms(name):
    delchars = str.maketrans({ ch : ch if str.isalpha(ch) else None for ch in map(chr, range(256))})
    words = [word.translate(delchars) for word in name.lower().split(' ')]
    return list(filter(lambda word: word != '', words))

class FamilyNameList(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    matching_families = models.ManyToManyField(Family, related_name='word_matches')

    @classmethod
    def ensure_indexed(cls, family):
        words = set()
        for partner in family.partners.all():
            for name in search_terms(partner.first_names):
                words.add(name.lower())
            for name in search_terms(partner.last_name):
                words.add(name.lower())
        for word in words:
            name_list, _created = FamilyNameList.objects.get_or_create(name=word)
            name_list.matching_families.add(family)
            name_list.save()

    @classmethod
    def search(cls, query):
        words = [word for word in search_terms(query)]

        if not words:
            return []

        # For each word, find the list of families that match that word.
        # Build a list of QuerySets, one for each word, and then OR them
        # together. This should result in only one DB query.
        querysets = [
            FamilyNameList.objects.filter(name__startswith=word) for word in words
        ]

        queryset = reduce(lambda a, b: a | b, querysets)

        result = set()
        # For each word->families match, count how many words each family matches.
        # Keep track of the maximum number of matches, and below discard those which
        # are less than the maximum.
        match_count = Counter()
        max_count = 0
        for family_name_list in queryset:
            for family in family_name_list.matching_families.all():
                match_count[family.id] += 1
                max_count = max(max_count, match_count[family.id])
                result.add(family)

        # Convert result to list, sorting by family name.
        result = list(filter(lambda family: match_count[family.id] == max_count, result))
        result.sort(key=lambda f: f.name)

        return result
