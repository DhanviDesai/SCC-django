from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics, viewsets
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

class NewsViewSet(viewsets.ModelViewSet):
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    authentication_classes = [FirebaseAuthentication]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['title']
    search_fields = ['^title']

    def get_queryset(self):
        if self.action == 'list':
            all_carousel_ids = News.objects.filter(is_carousel=True).order_by('-created_at').values_list('id', flat=True)
            other_carousel_ids = all_carousel_ids[3:]

            return News.objects.filter(
                Q(is_carousel=False) | Q(id__in=list(other_carousel_ids))
            ).order_by('-created_at')
        return News.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminRole]
        else:
            self.permission_classes = []
        return super().get_permissions()

class ListCarousel(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request):
        carousel_news = News.objects.filter(is_carousel=True).order_by('-created_at')[:3]
        serializer = NewsSerializer(carousel_news, many=True)
        return success_response(serializer.data, "Carousel news retrieved successfully.")
