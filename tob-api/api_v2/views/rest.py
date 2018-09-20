import base64

from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import NotFound
from rest_framework.decorators import detail_route, list_route
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response

from api_v2.serializers.rest import (
    IssuerSerializer,
    SchemaSerializer,
    CredentialTypeSerializer,
    TopicSerializer,
    CredentialSerializer,
    ExpandedCredentialSerializer,
    AddressSerializer,
    ContactSerializer,
    NameSerializer,
    CategorySerializer,
    PersonSerializer,
    CredentialTopicExtSerializer,
)

from rest_framework.serializers import SerializerMethodField

from api_v2.serializers.search import CustomTopicSerializer

from api_v2.models.Issuer import Issuer
from api_v2.models.Schema import Schema
from api_v2.models.CredentialType import CredentialType
from api_v2.models.Topic import Topic
from api_v2.models.Credential import Credential
from api_v2.models.Address import Address
from api_v2.models.Contact import Contact
from api_v2.models.Name import Name
from api_v2.models.Person import Person
from api_v2.models.Category import Category

from api_v2 import utils


class IssuerViewSet(ModelViewSet):
    serializer_class = IssuerSerializer
    queryset = Issuer.objects.all()

    @detail_route(url_path="credentialtype")
    def list_credential_types(self, request, pk=None):
        queryset = CredentialType.objects.filter(issuer__id=pk)
        get_object_or_404(queryset, pk=pk)
        serializer = CredentialTypeSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_path="logo")
    def fetch_logo(self, request, pk=None):
        issuer = get_object_or_404(self.queryset, pk=pk)
        logo = None
        if issuer.logo_b64:
            logo = base64.b64decode(issuer.logo_b64)
        if not logo:
            raise Http404()
        # FIXME - need to store the logo mime type
        return HttpResponse(logo, content_type="image/jpg")


class SchemaViewSet(ModelViewSet):
    serializer_class = SchemaSerializer
    queryset = Schema.objects.all()


class CredentialTypeViewSet(ModelViewSet):
    serializer_class = CredentialTypeSerializer
    queryset = CredentialType.objects.all()

    @detail_route(url_path="logo")
    def fetch_logo(self, request, pk=None):
        credType = get_object_or_404(self.queryset, pk=pk)
        logo = None
        if credType.logo_b64:
            logo = base64.b64decode(credType.logo_b64)
        elif credType.issuer and credType.issuer.logo_b64:
            logo = base64.b64decode(credType.issuer.logo_b64)
        if not logo:
            raise Http404()
        # FIXME - need to store the logo mime type
        return HttpResponse(logo, content_type="image/jpg")


class TopicViewSet(ModelViewSet):
    serializer_class = TopicSerializer
    queryset = Topic.objects.all()

    @detail_route(url_path="formatted")
    def retrieve_formatted(self, request, pk=None):
        item = self.get_object()
        serializer = CustomTopicSerializer(item)
        return Response(serializer.data)

    @detail_route(url_path="credential")
    def list_credentials(self, request, pk=None):
        item = self.get_object()
        queryset = item.credentials
        serializer = ExpandedCredentialSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_path="credential/active")
    def list_active_credentials(self, request, pk=None):
        item = self.get_object()
        queryset = item.credentials.filter(revoked=False)
        serializer = ExpandedCredentialSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(url_path="credential/historical")
    def list_historical_credentials(self, request, pk=None):
        item = self.get_object()
        queryset = item.credentials.filter(~Q(revoked=False))
        serializer = ExpandedCredentialSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path="ident/(?P<type>[^/.]+)/(?P<source_id>[^/.]+)")
    def retrieve_by_type(self, request, type=None, source_id=None):
        return self.retrieve(request)

    @list_route(methods=['get'], url_path="ident/(?P<type>[^/.]+)/(?P<source_id>[^/.]+)/formatted")
    def retrieve_by_type_formatted(self, request, type=None, source_id=None):
        return self.retrieve_formatted(request)

    def get_object(self):
        if self.kwargs.get("pk"):
            return super(TopicViewSet, self).get_object()

        type = self.kwargs.get("type")
        source_id = self.kwargs.get("source_id")
        if not type or not source_id:
            raise Http404()

        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, type=type, source_id=source_id)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class CredentialViewSet(ModelViewSet):
    serializer_class = CredentialSerializer
    queryset = Credential.objects.all()

    def retrieve(self, request, pk=None):
        queryset = self.queryset.filter(Q(wallet_id=pk) | Q(pk=pk))
        item = get_object_or_404(queryset)
        serializer = CredentialSerializer(item)
        return Response(serializer.data)

    @detail_route(url_path="formatted")
    def retrieve_formatted(self, request, pk=None):
        item = get_object_or_404(self.queryset, pk=pk)
        serializer = ExpandedCredentialSerializer(item)
        return Response(serializer.data)

    @list_route(url_path="active")
    def list_active(self, request, pk=None):
        queryset = self.queryset.filter(revoked=False)
        serializer = CredentialSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(url_path="historical")
    def list_historical(self, request, pk=None):
        queryset = self.queryset.filter(~Q(revoked=False))
        serializer = CredentialSerializer(queryset, many=True)
        return Response(serializer.data)


class AddressViewSet(ModelViewSet):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class ContactViewSet(ModelViewSet):
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()


class NameViewSet(ModelViewSet):
    serializer_class = NameSerializer
    queryset = Name.objects.all()


class PersonViewSet(ModelViewSet):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


# Add environment specific endpoints
try:
    utils.apply_custom_methods(TopicViewSet, "views", "TopicViewSet", "includeMethods")
except:
    pass
