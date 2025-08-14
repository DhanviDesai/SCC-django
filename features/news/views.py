from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole

from . serializers import NewsSerializer
from . models import News

# Create your views here.
class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListNews(generics.ListAPIView):
    authentication_classes = [FirebaseAuthentication]
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['title']
    search_fields = ['^title']

class AddNews(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    # Add some news
    def post(self, request):
        pass

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    # Update the news
    def put(self, request, news_id):
        pass

    # Delete the news
    def delete(self, request, news_id):
        pass

class ListCarousel(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        pass
