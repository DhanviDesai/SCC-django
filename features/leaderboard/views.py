from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
import logging
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce
from datetime import datetime

from features.tournament.models import Tournament
from features.activity.models import ActivityConfig, ActivityData, ActivityMetric
from features.utils.response_wrapper import error_response, success_response
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole

from . models import Leaderboard, TeamLeaderboard
from .serializers import DynamicLeaderboardSerializer, DynamicTeamLeaderboardSerializer, PublishedLeaderboardSerializer, PublishedTeamLeaderboardSerializer

logger = logging.getLogger(__name__)

# Create your views here.

# Create a view that creates leaderboard for the given tournament
class GetLeaderboard(APIView):
    def get_individual_tournament_leaderboard(self, activity, tournament: Tournament, start_date, end_date):
        # Build the ranking query
        ranked_participants = tournament.user.annotate(
            total_score=Coalesce(
                Sum(
                    'activity_data__metrics__value',
                    filter=
                        Q(activity_data__activity=tournament.activity) &
                        Q(activity_data__start_date__gte=start_date) &
                        Q(activity_data__start_date__lte=end_date)
                ),
                Value(0)  # If Sum returns NULL, use 0 instead
            )
        ).filter(total_score__gt=0).order_by('-total_score')
        objects = []
        for rank, rank_holder in enumerate(ranked_participants, start=1):
            objects.append({
                'tournament': tournament,
                'user': rank_holder,
                'rank': rank,
                'total_score': rank_holder.total_score
            })
        return objects

    def get_team_tournament_leaderboard(self, activity, tournament: Tournament, start_date, end_date):

        # Build the ranking query

        logger.info(start_date, end_date)

        ranked_teams = tournament.tournament_team.filter(is_registered=True).annotate(
            total_score=Coalesce(
                Sum(
                    'members__activity_data__metrics__value',
                    filter=
                        Q(members__activity_data__activity=tournament.activity) &
                        Q(members__activity_data__start_date__gte=start_date) &
                        Q(members__activity_data__start_date__lte=end_date)
                ),
                Value(0)  # If Sum returns NULL, use 0 instead
            )
        ).filter(total_score__gt=0).order_by('-total_score')
        objects = []
        for rank, team in enumerate(ranked_teams, start=1):
            objects.append({
                'tournament': tournament,
                'team': team,
                'rank': rank,
                'total_score': team.total_score
            })
        return objects

    def get(self, request, tournament_id):
        # Get the tournament by id
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        # Get the start_date and end_date from the request parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not start_date or not end_date:
            return error_response(message="start_date and end_date are required", status=status.HTTP_400_BAD_REQUEST)
        
        # Get the activity for the tournament
        activity = tournament.activity
        if not activity:
            return error_response(message="Activity not found for the tournament", status=status.HTTP_404_NOT_FOUND)
        
        if tournament.isIndividual():
            objects = self.get_individual_tournament_leaderboard(activity, tournament, start_date, end_date)
            leaderboard_serializer = DynamicLeaderboardSerializer(objects, many=True)
            return success_response(data=leaderboard_serializer.data, message="Leaderboard created successfully")
        elif tournament.isTeam():
            objects = self.get_team_tournament_leaderboard(activity, tournament, start_date, end_date)
            # Serialize the leaderboard objects
            leaderboard_serializer = DynamicTeamLeaderboardSerializer(objects, many=True)
            return success_response(data=leaderboard_serializer.data, message="Leaderboard created successfully")
        else:
            return error_response(message="Invalid tournament type", status=status.HTTP_400_BAD_REQUEST)


class GetPublishedLeaderboard(APIView):
    def get(self, request, tournament_id):
        # Get the tournament by id
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        if tournament.isIndividual():
            leaderboard_objects = Leaderboard.objects.filter(tournament=tournament).order_by('rank')
            leaderboard_serializer = PublishedLeaderboardSerializer(leaderboard_objects, many=True)
            return success_response(data=leaderboard_serializer.data, message="Published leaderboard fetched successfully")
        elif tournament.isTeam():
            leaderboard_objects = TeamLeaderboard.objects.filter(tournament=tournament).order_by('rank')
            leaderboard_serializer = PublishedTeamLeaderboardSerializer(leaderboard_objects, many=True)
            return success_response(data=leaderboard_serializer.data, message="Published leaderboard fetched successfully")
        else:
            return error_response(message="Invalid tournament type", status=status.HTTP_400_BAD_REQUEST)

class PublishLeaderboard(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, tournament_id):
        # The start date and end date would be sent in the request body
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        if not start_date or not end_date:
            return error_response(message="start_date and end_date are required", status=status.HTTP_400_BAD_REQUEST)
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        # Now we need to get the leaderboard for the tournament
        get_leaderboard_view = GetLeaderboard()
        if tournament.isIndividual():
            objects = get_leaderboard_view.get_individual_tournament_leaderboard(tournament.activity, tournament, start_date, end_date)
            # Save the objects to Leaderboard model
            for obj in objects:
                Leaderboard.objects.update_or_create(
                    tournament=obj['tournament'],
                    user=obj['user'],
                    start_date=start_date,
                    end_date=end_date,
                    defaults={
                        'rank': obj['rank'],
                        'total_score': obj['total_score'],
                    }
                )
            # Serialize the leaderboard objects
            leaderboard_serializer = PublishedLeaderboardSerializer(Leaderboard.objects.filter(tournament=tournament, start_date=start_date, end_date=end_date).order_by('rank'), many=True)
            return success_response(data=leaderboard_serializer.data, message="Leaderboard published successfully")
        elif tournament.isTeam():
            objects = get_leaderboard_view.get_team_tournament_leaderboard(tournament.activity, tournament, start_date, end_date)
            # Save the objects to TeamLeaderboard model
            for obj in objects:
                TeamLeaderboard.objects.update_or_create(
                    tournament=obj['tournament'],
                    team=obj['team'],
                    start_date=start_date,
                    end_date=end_date,
                    defaults={
                        'rank': obj['rank'],
                        'total_score': obj['total_score'],
                    }
                )
            # Serialize the leaderboard objects
            leaderboard_serializer = PublishedTeamLeaderboardSerializer(TeamLeaderboard.objects.filter(tournament=tournament, start_date=start_date, end_date=end_date).order_by('rank'), many=True)
            return success_response(data=leaderboard_serializer.data, message="Leaderboard published successfully")
        else:
            return error_response(message="Invalid tournament type", status=status.HTTP_400_BAD_REQUEST)