from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import City
from .serializers import CitySerializer

# Create your views here.
class CompanyPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListCity(generics.ListAPIView):
    queryset = City.objects.all().order_by('name')
    serializer_class = CitySerializer
    pagination_class = CompanyPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['^name']

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request):
        pass

    def put(self, request, city_id):
        pass

    def delete(self, request, city_id):
        pass