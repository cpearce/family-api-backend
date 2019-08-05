from rest_framework import serializers
from api.models import Individual, Family

class IndividualSerializer(serializers.ModelSerializer):
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
        self.spouse = others[0] if len(others) > 0 else None
        self.married_date = family.married_date
        self.married_location = family.married_location
        self.children = family.children.all()

class VerboseFamilySerializer(serializers.Serializer):
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
        self.parents = parents
        self.families = [VerboseFamily(individual, f) for f in families]

class VerboseIndividualSerializer(serializers.Serializer):
    individual = IndividualSerializer()
    families = VerboseFamilySerializer(many=True, required=False)
    parents = IndividualSerializer(many=True, required=False)
