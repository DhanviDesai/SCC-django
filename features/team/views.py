from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from uuid import uuid4

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from features.utils.response_wrapper import success_response, error_response
from features.users.models import User
from features.tournament.models import Tournament

from .models import Team
from .serializers import TeamSerializer

# Create your views here.
class ListTeams(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        uid = request.auth.get("user_id")
        user = User.objects.get(firebase_uid=uid)
        queryset = user.members.all()
        return success_response(data=TeamSerializer(queryset, many=True).data, message="Successfully fetched teams")

class ListAllTeams(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def get(self, request):
        return success_response(TeamSerializer(Team.objects.all(), many=True).data, message="Successfully fetched all the teams")

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request, id=None):
        if id is None:
            return error_response(message="Team id cannot be null")
        try:
            team = Team.objects.get(id=id)
            return success_response(data=TeamSerializer(team).data, message="Successfully fetched team data")
        except Exception:
            return error_response(message="Team not found", status=status.HTTP_404_NOT_FOUND)

# This is the view for the captain to create the team
# The idea is for the captain to create a team with a name and invite users from his company to join them
class CreateTeam(APIView):
    authentication_classes = [FirebaseAuthentication]
    def post(self, request):
        team_name = request.data.get("team_name")
        if team_name is None:
            return error_response(message="Team name cannot be null")
        tournament = request.data.get("tournament_id")
        if tournament is None:
            return error_response(message="Tournament id cannot be null")
        # Here, have to check if the user is already part of a team for this tournament
        user = User.objects.get(firebase_uid=request.auth.get("user_id"))
        try:
            target_tournament = Tournament.objects.get(id=tournament)
        except Exception:
            return error_response(message="Tournament not found")
        is_registered = user.members.filter(tournament=target_tournament).exists()
        if is_registered:
            return error_response(message="User is already part of a team for the tournament")
        team = Team.objects.create(id=uuid4(), name=team_name)
        team.members.add(user)
        team.tournament.add(target_tournament)
        return success_response(data=TeamSerializer(team).data, message="Successfully created a team", status=status.HTTP_200_OK)