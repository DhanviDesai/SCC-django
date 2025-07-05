from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from rest_framework import status
from uuid import uuid4
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from features.utils.storage import generate_presigned_url


from . models import Sport
from .serializers import SportSerializer

from features.sport_type.models import SportType
from features.utils.response_wrapper import success_response, error_response
from features.city.models import City
from features.tournament.models import Tournament

# Create your views here.
class SportPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class SportListView(generics.ListAPIView):
    queryset = Sport.objects.all().order_by('name')
    serializer_class = SportSerializer
    pagination_class = SportPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['^name']

    def get(self, request, *args, **kwargs):
        city_id = request.GET.get('city_id', None)
        if city_id is None:
            return super().get(self, request, *args, **kwargs)
        city = City.objects.get(id=city_id)
        self.queryset = Sport.objects.filter(sports__cities=city).distinct()
        return super().get(self, request, *args, **kwargs)


# class ListSport(APIView):
#     def get(self, request):
#         queryset = Sport.objects.all()
#         return success_response(data=SportSerializer(queryset, many=True).data, message="Sports fetched")

class AddSport(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        name = request.data.get('name', None)
        description = request.data.get('description', '')
        sport_type = request.data.get('sport_type')
        cover_image = request.data.get('cover_image')
        if name is None or sport_type is None:
            return error_response(message="name and sport_type cannot be null")
        sport_type_obj = SportType.objects.get(id=sport_type)
        if sport_type_obj is None:
            return error_response(message="sport_type not found")
        sport = Sport.objects.create(id=uuid4(), name=name, description=description, sport_type=sport_type_obj, cover_image=cover_image)
        return success_response(data=SportSerializer(sport).data, message="Sport created successfully", status=status.HTTP_201_CREATED)

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def put(self, request, sport_id):
        pass

    def delete(self, request, sport_id):
        if sport_id is None:
            return error_response(message="sport_id cannot be null")
        sport = Sport.objects.get(id=sport_id)
        sport.delete()
        return success_response(data=SportSerializer(sport).data, message="Sport deleted")

class GetPresignedUrl(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request):
        filename = request.GET.get('filename')
        filetype = request.GET.get('filetype')
        try:
            presigned_url, public_url = generate_presigned_url(f"sports/{filename}", filetype)
            data = {
                "presigned_url": presigned_url,
                "public_url": public_url
            }
            return success_response(data=data, message="Presigned url generated")
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))


