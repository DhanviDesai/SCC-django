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

from .serializers import TournamentTypeSerializer, TournamentSerializer, TournamentCreateSerializer, AddScheduleSerializer
from features.season.models import Season
from features.sport.models import Sport
from features.city.models import City
from features.users.models import User
from features.users.serializers import UserSerializer
from features.utils.storage import generate_presigned_url

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
        serializer = TournamentCreateSerializer(data=request.data)
        if serializer.is_valid():
            tournament = serializer.save(id=uuid4())
            return success_response(data=TournamentSerializer(tournament).data, message="Created tournament", status=status.HTTP_201_CREATED)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddSchedule(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        serializer = AddScheduleSerializer(data=request.data)
        if serializer.is_valid():
            try:
                tournament = Tournament.objects.get(id=serializer.validated_data['tournament_id'])
                tournament.schedule = serializer.validated_data['file_url']
                tournament.save()
                return success_response(message="Schedule updated successfully", status=status.HTTP_201_CREATED)
            except Tournament.DoesNotExist:
                return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetSchedulePresignedUrl(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def get(self, request):
        file_name = request.GET.get("filename")
        file_type = request.GET.get("filetype")

        try:
            presigned_url, public_url = generate_presigned_url(f"schedule/{file_name}", file_type)
            data = {
                "presigned_url": presigned_url,
                "public_url": public_url
            }
            return success_response(data=data, message="Presigned url generated")
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))

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
        # Individual cannot register to a team based tournament
        if not tournament.isIndividual:
            return error_response(message="Tournament is of type team")
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