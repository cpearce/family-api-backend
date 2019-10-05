from rest_framework import serializers
from api.models import Individual, Family, birth_date_or_min_year, married_date_or_min_year
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class IndividualSerializer(serializers.ModelSerializer):
    partner_in_families = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        fields = (
            'id',
            'first_names',
            'last_name',
            'sex',
            'birth_date',
            'birth_location',
            'death_date',
            'death_location',
            'buried_date',
            'buried_location',
            'baptism_date',
            'baptism_location',
            'occupation',
            'partner_in_families',
            'child_in_family',
            'note',
            'owner',
        )
        model = Individual

    @staticmethod
    def init_queryset(queryset):
        """ Perform necessary eager loading of data. """
        # See the following for details of what's going on here:
        # http://ses4j.github.io/2015/11/23/optimizing-slow-django-rest-framework-performance/
        queryset = queryset.select_related('child_in_family')
        queryset = queryset.prefetch_related(
            'partner_in_families'
        )
        return queryset

class FamilySerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        fields = (
            'id',
            'name',
            'married_date',
            'married_location',
            'partners',
            'children',
            'note',
            'owner',
        )
        read_only_fields = ['name']
        model = Family

    @staticmethod
    def init_queryset(queryset):
        """ Perform necessary eager loading of data. """
        # See the following for details of what's going on here:
        # http://ses4j.github.io/2015/11/23/optimizing-slow-django-rest-framework-performance/
        queryset = queryset.prefetch_related(
            'partners', 'children',
        )
        return queryset

class VerboseFamily:
    def __init__(self, individual, family):
        others = [p for p in family.partners.all() if p.id != individual.id]
        self.id = family.id
        self.spouse = others[0] if len(others) > 0 else None
        self.married_date = family.married_date
        self.married_location = family.married_location
        self.children = list(sorted(family.children.all(), key=birth_date_or_min_year))

class VerboseFamilySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    spouse = IndividualSerializer()
    married_date = serializers.DateField(required=False)
    married_location = serializers.CharField(max_length=100, required=False)
    children = IndividualSerializer(many=True, required=False)

# Serializes everything we need to render a detail page on an individual;
# the individual's details themselves, their parents details, and the
# details of their spouses and children.
class VerboseIndividual:
    def __init__(self, individual, families, parents):
        self.individual = individual
        self.parents = sorted(parents, key=birth_date_or_min_year)
        sorted_families = sorted(families, key=married_date_or_min_year)
        self.families = [VerboseFamily(individual, f) for f in sorted_families]
        self.parents_family = Family.objects.get(pk=individual.child_in_family.pk) if individual.child_in_family else None

class VerboseIndividualSerializer(serializers.Serializer):
    individual = IndividualSerializer()
    families = VerboseFamilySerializer(many=True, required=False)
    parents = IndividualSerializer(many=True, required=False)
    parents_family = FamilySerializer(required=False)

def has_write_access(user):
    perms = [
        'core.change_individual', 'core.change_child', 'core.change_family',
        'core.add_individual', 'core.add_child', 'core.add_family',
        'core.delete_individual', 'core.delete_child', 'core.delete_family'
    ]
    return all(map(lambda p: user.has_perm(p), perms))

class AccountDetail:
    def __init__(self, user):
        self.can_edit = has_write_access(user)

class AccountDetailSerializer(serializers.Serializer):
    can_edit = serializers.BooleanField(read_only=True)

class BasicIndividualSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    first_names = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    birth_date = serializers.DateField(required=False)
    death_date = serializers.DateField(required=False)

class BasicFamilySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    spouse = BasicIndividualSerializer(required=False)
    children = serializers.ListField(child=serializers.IntegerField())

class BasicIndividualAndFamiliesSerializer(serializers.Serializer):
    individual = BasicIndividualSerializer(required=True)
    families = BasicFamilySerializer(required=False, many=True)

class BasicIndividualWithParentsSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    first_names = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    birth_date = serializers.DateField(required=False)
    death_date = serializers.DateField(required=False)
    parents = serializers.ListField(child=serializers.IntegerField())

class BasicFamily:
    def __init__(self, individual, family):
        self.id = family.id
        partners = [i for i in family.partners.all() if i != individual]
        self.spouse = partners[0] if partners else None
        self.children = [
            child.id
            for child in family.children.all()
        ]

class BasicIndividual:
    def __init__(self, individual):
        self.id = individual.id
        self.first_names = individual.first_names
        self.last_name = individual.last_name
        self.birth_date = individual.birth_date
        self.death_date = individual.death_date

class BasicIndividualAndFamilies:
    def __init__(self, individual):
        self.individual = BasicIndividual(individual)
        self.families = [
            BasicFamily(individual, family)
            for family in individual.partner_in_families.all()
        ]

class BasicIndividualWithParents:
    def __init__(self, individual):
        self.id = individual.id
        self.first_names = individual.first_names
        self.last_name = individual.last_name
        self.birth_date = individual.birth_date
        self.death_date = individual.death_date
        self.parents = [p.id for p in individual.parents()]
