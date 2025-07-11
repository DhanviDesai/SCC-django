from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.response_wrapper import success_response, error_response
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from uuid import uuid4
from rest_framework import status

from .models import Tournament, TournamentType

from .serializers import TournamentTypeSerializer, TournamentSerializer
from features.season.models import Season
from features.sport.models import Sport
from features.city.models import City
from features.users.models import User
from features.users.serializers import UserSerializer

# Create your views here.
class TournamentTypeIndexOperations(APIView):
    def get(self, request):
        queryset = TournamentType.objects.all()
        return success_response(TournamentTypeSerializer(queryset, many=True).data, message="Tournament type fetched")

class TournamentPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListTournament(generics.ListAPIView):
    serializer_class = TournamentSerializer
    pagination_class = TournamentPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['^name']

    def get(self, request, *args, **kwargs):
        season_id = request.GET.get('season_id', None)
        if season_id is None:
            season_id = Season.objects.order_by('-created_at').first().id
        self.queryset = Tournament.objects.filter(season=season_id)
        return super().get(self, request, *args, **kwargs)

class AddTournament(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        name = request.data.get('name')
        if not name:
            return error_response(message="Name cannot be null")
        type = request.data.get('type')
        if not type:
            return error_response(message="Tournament type cannot be null")
        sport = request.data.get('sport')
        if not sport:
            return error_response(message="Sport cannot be null")
        cities = request.data.get('city')
        if not cities:
            return error_response(message="Cities cannot be null")
        season = request.data.get('season')
        if not season:
            return error_response(message="Season cannot be null")
        
        registration_start_date = request.data.get('registration_start_date')
        registration_end_date = request.data.get('registration_end_date')
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        description = request.data.get('description')

        type_obj = TournamentType.objects.get(id=type)
        sport_obj = Sport.objects.get(id=sport)
        season_obj = Season.objects.get(id=season)

        tournament = Tournament.objects.create(id=uuid4(), name=name, season=season_obj, sport=sport_obj, type=type_obj, description=description,
                                               registration_start_date=registration_start_date, registration_end_date=registration_end_date,
                                               start_date=start_date, end_date=end_date)
        for city in cities:
            tournament.cities.add(City.objects.get(id=city))
        tournament.save()
        return success_response(data=TournamentSerializer(tournament).data, message="Created tournament", status=status.HTTP_201_CREATED)

class DeleteTournament(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def delete(self, request, id):
        tournament = Tournament.objects.get(id=id)
        tournament.delete()
        return success_response(data=TournamentSerializer(tournament).data, message="Tournament Deleted")

class RegisterTournament(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be none")
        uid = request.auth.get("user_id")
        user = User.objects.get(firebase_uid=uid)
        tournament = Tournament.objects.get(id=id)
        user.tournament.add(tournament)
        return success_response(data=UserSerializer(user).data, message="Successfully registered to tournament", status=status.HTTP_200_OK)

class ListRegistrants(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=id)
            queryset = User.objects.filter(tournament=tournament)
            return success_response(data=UserSerializer(queryset, many=True).data, message="Registrants fetched")
        except Exception:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)

class GetTournament(APIView):
    def get(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=id)
            return success_response(data=TournamentSerializer(tournament).data, message="Tournament fetched successfully")
        except Exception:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)