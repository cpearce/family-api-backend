from rest_framework import generics
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.http import Http404

import pytz

from familyapi.settings import SITE_HOST, EMAIL_FROM_ADDRESS
from api.models import Individual, Family, PasswordResetRequest, FamilyNameList
from api.permissions import IsReadOnlyOrCanEdit, in_editors_group
from api.serializers import IndividualSerializer
from api.serializers import FamilySerializer
from api.serializers import VerboseIndividual, VerboseIndividualSerializer
from api.serializers import AccountDetail, AccountDetailSerializer
from api.serializers import BasicIndividualAndFamilies, BasicIndividualAndFamiliesSerializer
from api.serializers import BasicIndividualWithParents, BasicIndividualWithParentsSerializer

from smtplib import SMTPException

# Individual
class ListIndividual(generics.ListCreateAPIView):
    queryset = IndividualSerializer.init_queryset(Individual.objects.all())
    serializer_class = IndividualSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadOnlyOrCanEdit]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class DetailIndividual(generics.RetrieveUpdateDestroyAPIView):
    queryset = Individual.objects.all()
    serializer_class = IndividualSerializer
    permission_classes = [permissions.IsAuthenticated, IsReadOnlyOrCanEdit]

# Family
class ListFamily(generics.ListCreateAPIView):
    queryset = FamilySerializer.init_queryset(Family.objects.all())
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated, IsReadOnlyOrCanEdit]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class DetailFamily(generics.RetrieveUpdateDestroyAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated, IsReadOnlyOrCanEdit]

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
    families = FamilyNameList.search(pattern)
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

def populate_ancestors(individual, individuals):
    individuals.append(BasicIndividualWithParents(individual))
    for parent in individual.parents():
        populate_ancestors(parent, individuals)

@api_view(['GET'])
def individual_ancestors(request, pk):
    try:
        individual = Individual.objects.get(pk=pk)
    except Individual.DoesNotExist:
        raise Http404("Individual does not exist")
    individuals = []
    populate_ancestors(individual, individuals)
    serializer = BasicIndividualWithParentsSerializer(instance=individuals, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([])
def ping(request):
    """
    A watchdog; use this to kick the server to wake it up from Heroku's
    sleep mode. Frontend blocks on the reponse of this.
    """
    content = {
        'pong': True
    }
    return Response(content)

def account_already_exists(username, email):
    return (User.objects.filter(username=username).count() > 0 or
            User.objects.filter(email=email).count() > 0)

@api_view(['POST'])
def create_account(request):
    errors = []
    for field in ['username', 'email', 'first_name', 'last_name']:
        if not request.data.get(field):
            errors.append("Missing field '{}'".format(field))
            continue
        if len(request.data.get(field)) == 0:
            errors.append("Field '{}' cannot be blank".format(field))
        if len(request.data.get(field)) > 100:
            errors.append("Field '{}' cannot have length > 100".format(field))
    username = request.data.get('username')
    email = request.data.get('email')
    if account_already_exists(username, email):
        errors.append("Account with that username or email already exists")
    if errors:
        content = {
            'ok': False,
            'errors': errors,
        }
        return Response(status=400, data=content)

    new_user = User.objects.create_user(
        username,
        email=email,
        first_name=request.data.get('first_name'),
        last_name=request.data.get('last_name'),
    )

    editors_group = Group.objects.get(name='editors')
    new_user.groups.add(editors_group)
    new_user.save()

    pw_reset = PasswordResetRequest.create(user=new_user)

    send_confirmation_email = request.data.get('send_confirmation_email', True)

    if send_confirmation_email:
        message = (
            'To create your account on {},\nopen: https://{}/#confirm-account/{}'.format(
                SITE_HOST, SITE_HOST, pw_reset.token)
        )
        try:
            send_mail(
                'Please confirm your account on {}'.format(SITE_HOST),
                message,
                EMAIL_FROM_ADDRESS,
                [email],
                fail_silently=False,
            )
        except SMTPException as e:
            content = {
                'ok': False,
                'error': "SMTP error({}): {}".format(e.errno, e.strerror)
            }
            return Response(status=500, data=content)

        message = (
            'Account created for {} {}, {} '.format(
                new_user.first_name, new_user.last_name, new_user.email)
        )
        try:
            send_mail(
                'New user account created on {}'.format(SITE_HOST),
                message,
                EMAIL_FROM_ADDRESS,
                [EMAIL_FROM_ADDRESS],
                fail_silently=True,
            )
        except SMTPException:
            pass

    content = {
        'ok': True,
    }

    return Response(status=201, data=content)


@api_view(['POST'])
@permission_classes([])
def reset_password(request):
    token = request.data.get('token')
    password = request.data.get('password')
    errors = []
    if not token:
        errors.append('Please specify a token to reset.')
    if not password:
        errors.append('Please specify a new password to reset to.')
    if len(password) < 10:
        errors.append('Please specify a password at least 10 charcters longs.')
    if errors:
        return Response(status=400, data={
            'errors': errors,
        })

    pw_reset_request = PasswordResetRequest.find(token)
    if not pw_reset_request:
        return Response(status=400, data={
            'errors': ['Can\'t find valid password reset request for specified token.']
        })
    if not in_editors_group(pw_reset_request.user):
        return Response(status=400, data={
            'errors': ['Can\'t change password for non-editable users.']
        })
    pw_reset_request.user.set_password(password)
    pw_reset_request.user.save()

    send_confirmation_email = request.data.get('send_confirmation_email', True)
    if send_confirmation_email:
        try:
            user = pw_reset_request.user
            message = (
                'Password reset for {} {}, {} '.format(
                    user.first_name, user.last_name, user.email)
            )
            send_mail(
                'Password reset for user on {}'.format(SITE_HOST),
                message,
                EMAIL_FROM_ADDRESS,
                [EMAIL_FROM_ADDRESS],
                fail_silently=True,
            )
        except SMTPException:
            pass

    pw_reset_request.delete()

    return Response(status=200, data={
        'ok': True,
    })


@api_view(['POST'])
@permission_classes([])
def recover_account(request):
    email = request.data.get('email')
    if not email:
        return Response(status=200)
    count = User.objects.filter(email=email).count()
    if count == 0 or count > 1:
        # Not one unique user with this email.
        return Response(status=200)

    user = User.objects.filter(email=email).first()
    if not user:
        return Response(status=200)
    if not in_editors_group(user):
        # Can't change password for non-editable users.
        return Response(status=200)

    pw_reset_request = PasswordResetRequest.create(user)

    send_confirmation_email = request.data.get('send_confirmation_email', True)

    if send_confirmation_email:
        message = (
            """
            To reset the password for your account on {},
            with username: {},
            open:\nhttps://{}/#reset-password/{}
            """.format(SITE_HOST, user.username, SITE_HOST, pw_reset_request.token)
        )

        try:
            send_mail(
                'Password reset request for {}'.format(SITE_HOST),
                message,
                EMAIL_FROM_ADDRESS,
                [email],
                fail_silently=True,
            )
        except SMTPException as _:
            # Fail silently.
            pass

    return Response(status=200)
