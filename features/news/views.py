from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from features.utils.response_wrapper import success_response, error_response
from rest_framework import status

from django.db.models import Q
from . serializers import NewsSerializer
from . models import News

# Create your views here.
class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListNews(generics.ListAPIView):
    authentication_classes = [FirebaseAuthentication]
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['title']
    search_fields = ['^title']

    def get_queryset(self):
        all_carousel_ids = News.objects.filter(is_carousel=True).order_by('-created_at').values_list('id', flat=True)
        other_carousel_ids = all_carousel_ids[3:]

        return News.objects.filter(
            Q(is_carousel=False) | Q(id__in=list(other_carousel_ids))
        ).order_by('-created_at')

class AddNews(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "News added successfully.", status=status.HTTP_201_CREATED)
        return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def put(self, request, id):
        try:
            news = News.objects.get(id=id)
        except News.DoesNotExist:
            return error_response("News not found.", status=status.HTTP_404_NOT_FOUND)

        serializer = NewsSerializer(news, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "News updated successfully.")
        return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            news = News.objects.get(id=id)
        except News.DoesNotExist:
            return error_response("News not found.", status=status.HTTP_404_NOT_FOUND)

        news.delete()
        return success_response(message="News deleted successfully.")

class ListCarousel(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request):
        carousel_news = News.objects.filter(is_carousel=True).order_by('-created_at')[:3]
        serializer = NewsSerializer(carousel_news, many=True)
        return success_response(serializer.data, "Carousel news retrieved successfully.")
