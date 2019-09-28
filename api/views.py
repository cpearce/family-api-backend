from rest_framework import generics
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import CharField, Value
from django.db.models.functions import Concat

from api.models import Individual, Family
from api.serializers import IndividualSerializer
from api.serializers import FamilySerializer
from api.serializers import VerboseIndividual, VerboseIndividualSerializer
from api.serializers import AccountDetail, AccountDetailSerializer
from api.serializers import BasicIndividualAndFamilies, BasicIndividualAndFamiliesSerializer

# Individual
class ListIndividual(generics.ListCreateAPIView):
    queryset = IndividualSerializer.init_queryset(Individual.objects.all())
    serializer_class = IndividualSerializer

class DetailIndividual(generics.RetrieveUpdateDestroyAPIView):
    queryset = Individual.objects.all()
    serializer_class = IndividualSerializer

# Family
class ListFamily(generics.ListCreateAPIView):
    queryset = FamilySerializer.init_queryset(Family.objects.all())
    serializer_class = FamilySerializer

class DetailFamily(generics.RetrieveUpdateDestroyAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

@api_view(['GET'])
def account_details(request):
    if request.method != 'GET':
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if request.user is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    serializer = AccountDetailSerializer(AccountDetail(request.user))
    return Response(serializer.data)

@api_view(['GET'])
def list_family_of_individual(request, pk):
    if request.method != 'GET':
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        individual = Individual.objects.get(pk=pk)
    except Snippet.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    families = individual.partner_in_families.all()
    serializer = FamilySerializer(families, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def verbose_individual_detail(request, pk):
    if request.method != 'GET':
        # TODO: Verify whether this is actually needed.
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        individual = Individual.objects.get(pk=pk)
    except Snippet.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    families = individual.partner_in_families.all()
    parents = individual.parents()
    serializer = VerboseIndividualSerializer(
        VerboseIndividual(individual, families, parents))
    return Response(serializer.data)

@api_view(['POST'])
def logout(request):
    if request.method != 'POST':
        # TODO: Verify whether this is actually needed.
        return Response(status=status.HTTP_400_BAD_REQUEST)
    request.user.auth_token.delete()
    return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
def search_individuals(request, pattern):
    individuals = list(Individual.objects.annotate(
        full_name=Concat(
            'first_names', Value(' '), 'last_name',
            output_field=CharField(max_length=100)
        )
    ).filter(full_name__icontains=pattern))
    individuals.sort(key=lambda i: i.last_name)
    individuals.sort(key=lambda i: i.first_names)
    serializer = IndividualSerializer(instance=individuals, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def search_families(request, pattern):
    families = list(Family.objects.filter(name__icontains=pattern))
    families.sort(key=lambda f: f.name)
    serializer = FamilySerializer(instance=families, many=True)
    return Response(serializer.data)

def populate_descendants(individual, individuals):
    families = individual.partner_in_families.all()
    individuals.append(BasicIndividualAndFamilies(individual))
    for family in families:
        for child in family.children.all():
            populate_descendants(child, individuals)

@api_view(['GET'])
def individual_desendants(request, pk):
    try:
        individual = Individual.objects.get(pk=pk)
    except Individual.DoesNotExist:
        raise Http404("Individual does not exist")
    individuals = []
    populate_descendants(individual, individuals)
    serializer = BasicIndividualAndFamiliesSerializer(instance=individuals, many=True)
    return Response(serializer.data)
