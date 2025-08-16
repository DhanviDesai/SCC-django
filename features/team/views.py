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
from features.utils.messaging import send_fcm_notification

from .models import Team, Invite, InviteStatus
from .serializers import TeamSerializer, InviteSerializer

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
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found")
        is_registered = user.members.filter(tournament=target_tournament).exists()
        if is_registered:
            return error_response(message="User is already part of a team for the tournament")
        team = Team.objects.create(id=uuid4(), name=team_name, created_by=user)
        team.members.add(user)
        team.tournament.add(target_tournament)
        return success_response(data=TeamSerializer(team).data, message="Successfully created a team", status=status.HTTP_200_OK)

class InviteUser(APIView):
    authentication_classes = [FirebaseAuthentication]
    def post(self, request, team_id=None):
        print(f"Here in invite user {team_id}")
        if team_id is None:
            return error_response(message="Team id cannot be null")
        # These are the users being invited
        user_id = request.data.get("user_id")
        if user_id is None:
            return error_response(message="User id cannot be null or empty")
        try:
            invitee = User.objects.get(firebase_uid=user_id)
        except User.DoesNotExist:
            return error_response(message="Invitee not found")
        # This is the inviter
        inviter = User.objects.get(firebase_uid=request.auth.get("user_id"))
        if not invitee.company == inviter.company:
            return error_response(message="Invitee does not belong to the same company")
        try:
            team = Team.objects.get(id=team_id)
        except:
            return error_response(message="Team not found")
        tournament_id = request.data.get('tournament_id')
        if tournament_id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        if tournament is None:
            return error_response(message="Tournament cannot be null")
        
        invite_exists = Invite.objects.filter(team=team, tournament=tournament, inviter=inviter, invitee=invitee).exists()
        if invite_exists:
            return error_response(message="Invite already exists")
        now = datetime.now()
        invite = Invite.objects.create(id=uuid4(), team=team, tournament=tournament, invitee=invitee, inviter=inviter, created_at=now, updated_at=now, status=InviteStatus.PENDING)
        # Send a notification to invitee
        if invitee.fcm_token:
            # NOTIFICATION
            body_message = f"You have been invited to join the team {team.name} for the tournament {tournament.name}"
            if send_fcm_notification(invitee.fcm_token, title="Team invite", body=body_message):
                print("Notification successful")
        return success_response(message="User invited successfully", data=InviteSerializer(invite).data)

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

# Any invite should be rejected/accepted within the registration deadline

# Once the invite is accepted, if there are enough members in the team, the team would be registered to the tournament
# Once the team is registered, all other invites for the team would expire

class AcceptInvite(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, invite_id=None):
        # Update the invite status to accepted
        # Add the user as a member into the team
        # Just call the registerTournament endpoint
        if not invite_id:
            return error_response(message="Invite id cannot be null")
        try:
            invite = Invite.objects.get(id=invite_id)
        except Invite.DoesNotExist:
            return error_response(message="Invite not found", status=status.HTTP_404_NOT_FOUND)
        
        if not invite.status == InviteStatus.PENDING:
            return error_response(message="Invite is invalid")
        
        # This is the user who accepted the invite
        user = request.auth.get('user_id')

        # Update the invite status
        invite.status = InviteStatus.ACCEPTED
        invite.save()

        # Add the user as a team member
        team = invite.team
        team.members.add(user)
        team.save()

        # Check if team has enough members and register if it has enough
        if invite.team.members.count() == invite.tournament.team_size:
            team.is_registered = True
            team.save()

            # Here, send the notification to the captain or team creater that his team is registered
            # NOTIFICATION
            body = f"Congrats! Your team {team.name} is registered to tournament {team.tournament.name}"
            if send_fcm_notification(team.created_by.fcm_token, title="Team registered", body=body):
                print("Notification sent successfully")
            # Invalidate all other invites for the same team and tournament
            Invite.objects.filter(team=invite.team, tournament=invite.tournament, status=InviteStatus.PENDING).update(status=InviteStatus.EXPIRED)
        return success_response(message="Invite accepted successfully", status=status.HTTP_200_OK)


class RejectInvite(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, invite_id=None):
        # Update the status of invite to rejected
        if invite_id is None:
            return error_response(message="Invite id cannot be null")
        
        try:
            invite = Invite.objects.get(id=invite_id)
        except Invite.DoesNotExist:
            return error_response(message="Invite not found", status=status.HTTP_404_NOT_FOUND)
        
        invite.status = InviteStatus.REJECTED
        invite.save()

        return success_response(message="Invite rejected successfully")
        
# TODO
class RegisterTournament(APIView):
    authentication_classes = [FirebaseAuthentication]
    def put(self, request, team_id=None):
        if team_id is None:
            return error_response(message="Team id cannot be null")
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return error_response(message="Team not found", status=status.HTTP_404_NOT_FOUND)
        tournament_id = request.data.get("tournament_id")
        if tournament_id is None:
            return error_response(message="Tournament id cannot be null")
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        # If the total number of members in the team are more than minimum required for a team, update the is_registered flag to true
        pass