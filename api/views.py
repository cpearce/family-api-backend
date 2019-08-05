from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers

from api.models import Individual, Family
from api.serializers import IndividualSerializer, FamilySerializer, VerboseIndividual, VerboseIndividualSerializer

# Individual
class ListIndividual(generics.ListCreateAPIView):
    queryset = Individual.objects.all()
    serializer_class = IndividualSerializer

class DetailIndividual(generics.RetrieveUpdateDestroyAPIView):
    queryset = Individual.objects.all()
    serializer_class = IndividualSerializer

# Family
class ListFamily(generics.ListCreateAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

class DetailFamily(generics.RetrieveUpdateDestroyAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

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
    # if not serializer.is_valid():
    #     return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.data)
