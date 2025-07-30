from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from uuid import uuid4
from datetime import datetime

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from features.utils.response_wrapper import success_response, error_response
from features.users.models import User
from features.tournament.models import Tournament

from .models import Team, Invite
from .serializers import TeamSerializer, InviteSerializer, CreateTeamSerializer, InviteUserSerializer

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
        serializer = CreateTeamSerializer(data=request.data)
        if serializer.is_valid():
            team_name = serializer.validated_data['team_name']
            tournament_id = serializer.validated_data['tournament_id']
            user = User.objects.get(firebase_uid=request.auth.get("user_id"))
            try:
                target_tournament = Tournament.objects.get(id=tournament_id)
            except Tournament.DoesNotExist:
                return error_response(message="Tournament not found")
            is_registered = user.members.filter(tournament=target_tournament).exists()
            if is_registered:
                return error_response(message="User is already part of a team for the tournament")
            team = Team.objects.create(id=uuid4(), name=team_name, created_by=user)
            team.members.add(user)
            team.tournament.add(target_tournament)
            return success_response(data=TeamSerializer(team).data, message="Successfully created a team", status=status.HTTP_200_OK)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InviteUser(APIView):
    authentication_classes = [FirebaseAuthentication]
    def post(self, request, team_id=None):
        if team_id is None:
            return error_response(message="Team id cannot be null")
        serializer = InviteUserSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                invitee = User.objects.get(firebase_uid=user_id)
            except User.DoesNotExist:
                return error_response(message="Invitee not found")

            inviter = User.objects.get(firebase_uid=request.auth.get("user_id"))
            try:
                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                return error_response(message="Team not found")

            now = datetime.now()
            invite = Invite.objects.create(id=uuid4(), team=team, invitee=invitee, inviter=inviter, created_at=now, updated_at=now)
            # Maybe here some notification can also be triggered
            return success_response(message="User invited successfully")
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListReceivedInvites(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        user = User.objects.get(firebase_uid=request.auth.get("user_id"))
        queryset = Invite.objects.filter(invitee=user)
        return success_response(InviteSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

class ListSentInvites(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        user = User.objects.get(firebase_uid=request.auth.get("user_id"))
        queryset = Invite.objects.filter(inviter=user)
        return success_response(InviteSerializer(queryset, many=True).data, status=status.HTTP_200_OK)
