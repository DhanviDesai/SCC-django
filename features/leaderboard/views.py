from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
import logging

from features.tournament.models import Tournament
from features.activity.models import ActivityConfig, ActivityData, ActivityMetric
from features.utils.response_wrapper import error_response, success_response

from . models import Leaderboard
from .serializers import LeaderboardSerializer

logger = logging.getLogger(__name__)

# Create your views here.

# Create a view that creates leaderboard for the given tournament
class GetLeaderboard(APIView):
    def get(self, request, tournament_id):
        # Get the tournament by id
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return error_response(message="Tournament not found", status=status.HTTP_404_NOT_FOUND)
        
        # Get the activity for the tournament
        activity = tournament.activity
        if not activity:
            return error_response(message="Activity not found for the tournament", status=status.HTTP_404_NOT_FOUND)
        
        # Get all the activity data for the users registered to the tournament
        activity_data = ActivityData.objects.filter(activity=activity, user__in=tournament.user.all())

        logger.info(activity_data)

        # Get the metrics for the activity
        metrics = ActivityMetric.objects.filter(activity_data__in=activity_data)

        logger.info(metrics)

        # Now rank the users based on the values in metrics
        # leaderboard[user_id] = {'user': user, 'values': {'metric_1': value_1, 'metric_2': value_2, ...}}
        leaderboard = {}
        for metric in metrics:
            user_id = metric.activity_data.user.firebase_uid
            if user_id not in leaderboard:
                leaderboard[user_id] = {
                    'user': metric.activity_data.user,
                    'values': {}
                }
            leaderboard[user_id]['values'][metric.metric.metric_type] = leaderboard[user_id]['values'].get(metric.metric.metric_type, 0) + metric.value
        # Sort the leaderboard based on all the metrics
        sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: sum(x[1]['values'].values()), reverse=True)
        print(sorted_leaderboard)
        # Create the leaderboard objects
        leaderboard_objects = []
        for rank, (user_id, user_data) in enumerate(sorted_leaderboard, start=1):
            leaderboard_objects.append({
                'tournament': tournament,
                'user': user_data['user'],
                'rank': rank
            })
        # Save the leaderboard objects
        for leaderboard_object in leaderboard_objects:
            leaderboard_entry, created = Leaderboard.objects.update_or_create(
                tournament=leaderboard_object['tournament'],
                user=leaderboard_object['user'],
                defaults={'rank': leaderboard_object['rank']}
            )
        # Serialize the leaderboard objects
        leaderboard_serializer = LeaderboardSerializer(Leaderboard.objects.filter(tournament=tournament).order_by('rank'), many=True)
        return success_response(data=leaderboard_serializer.data, message="Leaderboard created successfully", status=status.HTTP_201_CREATED)
