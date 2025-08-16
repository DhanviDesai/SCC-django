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

from .models import Tournament, TournamentType, OnlineIndividualData, TournamentStatus

from .serializers import TournamentTypeSerializer, TournamentSerializer
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
        if not registration_start_date:
            return error_response(message="Registration start date cannot be null")
        registration_end_date = request.data.get('registration_end_date')
        if not registration_end_date:
            return error_response(message="Registration end date cannot be null")
        start_date = request.data.get('start_date')
        if not start_date:
            return error_response(message="Start date cannot be null")
        end_date = request.data.get('end_date')
        if not end_date:
            return error_response(message="End date cannot be null")
        
        description = request.data.get('description')
        team_size = request.data.get('team_size')

        type_obj = TournamentType.objects.get(id=type)
        if "team" in type_obj.name and not team_size:
            return error_response(message="Team size cannot be null for team type tournament")
        sport_obj = Sport.objects.get(id=sport)
        season_obj = Season.objects.get(id=season)

        tournament = Tournament.objects.create(id=uuid4(), name=name, season=season_obj, sport=sport_obj, type=type_obj, description=description,
                                               registration_start_date=registration_start_date, registration_end_date=registration_end_date,
                                               start_date=start_date, end_date=end_date)
        for city in cities:
            tournament.cities.add(City.objects.get(id=city))
        tournament.save()
        return success_response(data=TournamentSerializer(tournament).data, message="Created tournament", status=status.HTTP_201_CREATED)

class AddSchedule(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        file_url = request.data.get("file_url")
        if file_url is None:
            return error_response(message="File url cannot be null")
        tournament_id = request.data.get("tournament_id")
        if tournament_id is None:
            return error_response(message="Tournament cannot be null")
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            tournament.schedule = file_url
            tournament.save()
            return success_response(message="Schedule updated successfully", status=status.HTTP_201_CREATED)
        except Exception:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)

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
        tournament.status = TournamentStatus.DELETED
        tournament.save()
        data = TournamentSerializer(tournament).data
        return success_response(data=data, message="Tournament Deleted")

class RegisterTournament(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be none")
        uid = request.auth.get("user_id")
        user = User.objects.get(firebase_uid=uid)
        try:
            tournament = Tournament.objects.get(id=id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        # Individual cannot register to a team based tournament
        if not tournament.isIndividual():
            return error_response(message="Tournament is of type team")
        tournament.user.add(user)
        return success_response(data=UserSerializer(user).data, message="Successfully registered to tournament", status=status.HTTP_200_OK)

class ListRegistrants(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        queryset = tournament.user.all()
        return success_response(data=UserSerializer(queryset, many=True).data, message="Registrants fetched")

class IndexOperations(APIView):
    def get(self, request, id=None):
        if id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=TournamentSerializer(tournament).data, message="Tournament fetched successfully")
    
    def put(self, request, id=None):
        if id is None:
            return error_response(message="Tournamet id cannot be null")
        try:
            tournament = Tournament.objects.get(id=id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        name = request.data.get('name')
        if name:
            tournament.name = name
        start_date = request.data.get('start_date')
        if start_date:
            tournament.start_date = start_date
        end_date = request.data.get('end_date')
        if end_date:
            tournament.end_date = end_date
        registration_start_date = request.data.get('registration_start_date')
        if registration_start_date:
            tournament.registration_start_date = registration_start_date
        registration_end_date = request.data.get('registration_end_date')
        if registration_end_date:
            tournament.registration_end_date = registration_end_date
        description = request.data.get('description')
        if description:
            tournament.description = description
        team_size = request.data.get('team_size')
        if team_size:
            tournament.team_size = team_size
        tournament.save()
        return success_response(data=TournamentSerializer(tournament).data, message="Tournament updated successfully")

# This would require smart job for leaderboard.
# The job has to know whether to sort by ascending or descending
class HandleIncomingData(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, tournament_id=None):
        if tournament_id is None:
            return error_response(message="Tournament cannot be null")
        # Get the tournament
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        # Check whether this user has registered to this tournament
        user_id = request.auth.get("user_id")
        if not tournament.user.filter(firebase_uid=user_id).exists():
            return error_response(message="User has not registered to the tournament")
        # User has registered to the tournament
        # How should the data be uploaded? Let's give a list of data where each object should have date and count
        data_list = request.data.get("data")
        if data_list is None:
            return error_response(message="Data cannot be null")
        
        # Get the tournament type
        if tournament.isIndividual() and tournament.isOnline():
            # Update the data in online individual table
            for data in data_list:
                date = data["date"]
                count = data["count"]
                row = OnlineIndividualData.objects.update_or_create(
                    tournament=tournament,
                    user=User.objects.get(firebase_uid=user_id),
                    entry_date=date,
                    defaults={ "data": int(count) }
                )
            return success_response(message="Successfully updated")
        if tournament.isTeam() and tournament.isOnline():
            # Update the data in online team table
            pass
        return error_response(message="This is to only update for online tournaments")
