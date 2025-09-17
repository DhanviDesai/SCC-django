from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
import uuid

from .models import City
from .serializers import CitySerializer

from features.utils.response_wrapper import success_response, error_response

# Create your views here.
class CityPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListCity(generics.ListAPIView):
    queryset = City.objects.all().order_by('name')
    serializer_class = CitySerializer
    pagination_class = CityPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['^name']

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return error_response(message="Name is required", status=400)
        state = request.data.get('state')
        if not state:
            return error_response(message="State is required", status=400)
        if City.objects.filter(name=name, state=state).exists():
            return error_response(message="City with this name and state already exists", status=400)
        city = City.objects.create(id=uuid.uuid4(), name=name, state=state)
        serializer = CitySerializer(city)
        return success_response(data=serializer.data, message="City created successfully", status=201)

    def put(self, request, city_id):
        pass

    def delete(self, request, city_id):
        pass