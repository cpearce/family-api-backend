from rest_framework import serializers
from api.models import Individual, Family, birth_date_or_min_year, married_date_or_min_year

class IndividualSerializer(serializers.ModelSerializer):
    partner_in_families = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        fields = '__all__'
        model = Individual

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'married_date',
            'married_location',
            'partners',
            'children',
        )
        model = Family

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

class VerboseIndividualSerializer(serializers.Serializer):
    individual = IndividualSerializer()
    families = VerboseFamilySerializer(many=True, required=False)
    parents = IndividualSerializer(many=True, required=False)
