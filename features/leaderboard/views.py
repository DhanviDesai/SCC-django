from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
import logging
from django.db.models import Sum, Q, Value
from django.db.models.functions import Coalesce

from features.tournament.models import Tournament
from features.activity.models import ActivityConfig, ActivityData, ActivityMetric
from features.utils.response_wrapper import error_response, success_response
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole

from . models import Leaderboard, TeamLeaderboard, PublishedLeaderboard, PublishedTeamLeaderboard
from .serializers import LeaderboardSerializer, TeamLeaderboardSerializer

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
        logger.info(f"django query: {ranked_participants}")
        rank = 1
        objects = []
        for rank_holder in ranked_participants:
            objects.append({
                'tournament': tournament,
                'user': rank_holder,
                'rank': rank
            })
            rank += 1

        for leaderboard_object in objects:
            leaderboard_entry, created = Leaderboard.objects.update_or_create(
                tournament=leaderboard_object['tournament'],
                user=leaderboard_object['user'],
                defaults={'rank': leaderboard_object['rank']}
            )
        # Serialize the leaderboard objects
        leaderboard_serializer = LeaderboardSerializer(Leaderboard.objects.filter(tournament=tournament).order_by('rank'), many=True)
        return success_response(data=leaderboard_serializer.data, message="Leaderboard created successfully")

    def get_team_tournament_leaderboard(self, activity, tournament: Tournament, start_date, end_date):

        # Build the ranking query

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
        objects = {}
        for rank, team in enumerate(ranked_teams, start=1):
            objects[team.id] = {
                'tournament': tournament,
                'team': team,
                'rank': rank
            }



        # Get all the teams registered to the tournament
        # teams = tournament.tournament_team.all()
        # if not teams:
        #     return error_response(message="No teams registered to the tournament", status=status.HTTP_404_NOT_FOUND)
        # # Rank the teams based on the activity data of their members
        # leaderboard = {}
        # for team in teams:
        #     team_members = team.members.all()
        #     activity_data = ActivityData.objects.filter(activity=activity, user__in=team_members, start_date__gte=start_date, end_date__lte=end_date)
        #     metrics = ActivityMetric.objects.filter(activity_data__in=activity_data)
        #     team_score = 0
        #     for metric in metrics:
        #         team_score += metric.value
        #     leaderboard[team.id] = {
        #         'team': team,
        #         'score': team_score
        #     }
        # # Sort the leaderboard based on the team score
        # sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1]['score'], reverse=True)
        # # Create the leaderboard objects
        # leaderboard_objects = []
        # for rank, (team_id, team_data) in enumerate(sorted_leaderboard, start=1):
        #     leaderboard_objects.append({
        #         'tournament': tournament,
        #         'team': team_data['team'],
        #         'rank': rank
            # })
        # Save the leaderboard objects
        for leaderboard_object in objects.values():
            leaderboard_entry, created = TeamLeaderboard.objects.update_or_create(
                tournament=leaderboard_object['tournament'],
                team=leaderboard_object['team'],
                defaults={'rank': leaderboard_object['rank']}
            )
        # Serialize the leaderboard objects
        leaderboard_serializer = TeamLeaderboardSerializer(TeamLeaderboard.objects.filter(tournament=tournament).order_by('rank'), many=True)
        return success_response(data=leaderboard_serializer.data, message="Leaderboard created successfully")

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
            return self.get_individual_tournament_leaderboard(activity, tournament, start_date, end_date)
        elif tournament.isTeam():
            return self.get_team_tournament_leaderboard(activity, tournament, start_date, end_date)
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
            try:
                published_leaderboard = PublishedLeaderboard.objects.get(tournament=tournament)
            except PublishedLeaderboard.DoesNotExist:
                return error_response(message="Published leaderboard not found", status=status.HTTP_404_NOT_FOUND)
            leaderboard_serializer = LeaderboardSerializer(Leaderboard.objects.filter(tournament=tournament).order_by('rank'), many=True)
            return success_response(data={
                'published_at': published_leaderboard.published_at,
                'leaderboard': leaderboard_serializer.data
            }, message="Published leaderboard retrieved successfully")
        elif tournament.isTeam():
            try:
                published_leaderboard = PublishedTeamLeaderboard.objects.get(tournament=tournament)
            except PublishedTeamLeaderboard.DoesNotExist:
                return error_response(message="Published leaderboard not found", status=status.HTTP_404_NOT_FOUND)
            leaderboard_serializer = TeamLeaderboardSerializer(TeamLeaderboard.objects.filter(tournament=tournament).order_by('rank'), many=True)
            return success_response(data={
                'published_at': published_leaderboard.published_at,
                'leaderboard': leaderboard_serializer.data
            }, message="Published leaderboard retrieved successfully")
        else:
            return error_response(message="Invalid tournament type", status=status.HTTP_400_BAD_REQUEST)

class PublishLeaderboard(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def post(self, request, tournament_id):
        # Get the tournament by id
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        if tournament.isIndividual():
            # Check if the leaderboard exists
            leaderboard_exists = Leaderboard.objects.filter(tournament=tournament).exists()
            if not leaderboard_exists:
                return error_response(message="Leaderboard not found for the tournament", status=status.HTTP_404_NOT_FOUND)
            # Drop all the existing published leaderboard entries for the tournament
            PublishedLeaderboard.objects.filter(tournament=tournament).delete()
            # Create the published leaderboard entries
            PublishedLeaderboard.objects.bulk_create(Leaderboard.objects.filter(tournament=tournament), ignore_conflicts=True)
            return success_response(message="Leaderboard published successfully", status=status.HTTP_201_CREATED)
        elif tournament.isTeam():
            # Check if the leaderboard exists
            leaderboard_exists = TeamLeaderboard.objects.filter(tournament=tournament).exists()
            if not leaderboard_exists:
                return error_response(message="Leaderboard not found for the tournament", status=status.HTTP_404_NOT_FOUND)
            # Drop all the existing published leaderboard entries for the tournament
            PublishedTeamLeaderboard.objects.filter(tournament=tournament).delete()
            # Create the published leaderboard entries
            PublishedTeamLeaderboard.objects.bulk_create(TeamLeaderboard.objects.filter(tournament=tournament).values_list('tournament', 'team', 'rank'), ignore_conflicts=True)
            return success_response(message="Leaderboard published successfully", status=status.HTTP_201_CREATED)
        else:
            return error_response(message="Invalid tournament type", status=status.HTTP_400_BAD_REQUEST)