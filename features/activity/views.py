from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
import logging
import json

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from features.users.models import User
from features.utils.response_wrapper import success_response, error_response
from features.metric.models import MetricConfig

from . models import ActivityConfig, ActivityMetric, ActivityData
from .serializers import ActivityConfigReadSerializer, ActivityConfigWriteSerializer, ActivityDataSerializer
from datetime import datetime

logger = logging.getLogger(__name__)

# Create your views here.
class ActivityConfigViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    queryset = ActivityConfig.objects.all()

    # Handle OPTIONS request and return allowed methods with 204 status
    def options(self, request, *args, **kwargs):
        response = super().options(request, *args, **kwargs)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ActivityConfigWriteSerializer
        return ActivityConfigReadSerializer

class ActivityDataListView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def get(self, request, activity_id=None):
        # Placeholder for future implementation
        try:
            activity_data = ActivityData.objects.get(id=activity_id)
        except ActivityData.DoesNotExist:
            return error_response(message="Activity data not found", status=404)
        return success_response(data=ActivityDataSerializer(activity_data).data, message="Activity data retrieved successfully")

class ActivityDataPostView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def post(self, request):
        # Get the user
        user = User.objects.get(firebase_uid=request.auth.get('user_id'))

        # Check whether the activity exists
        try:
            activity = ActivityConfig.objects.get(id=request.data.get('activity'))
        except ActivityConfig.DoesNotExist:
            return error_response(message="Activity not found", status=404)
        
        # Upsert the metric values for the activity of the user at the given start_date
        try:
            start_date = datetime.fromisoformat(request.data.get('start_datetime')).date()
        except ValueError:
            return error_response(message="Invalid start_datetime format", status=400)
        end_date = None
        if request.data.get('end_datetime'):
            try:
                end_date = datetime.fromisoformat(request.data.get('end_datetime')).date()
            except ValueError:
                return error_response(message="Invalid end_datetime format", status=400)
        activity_data, created = ActivityData.objects.get_or_create(
            user=user,
            activity=activity,
            start_date=start_date,
            defaults={'end_date': end_date}
        )
        
        # Get all the ActivityMetric objects for the activity_data
        existing_metrics = {am.metric.id: am for am in ActivityMetric.objects.filter(activity_data=activity_data)}
        
        # Update the ActivityMetric object values from the metrics in the request
        for metric in request.data.get('metrics', []):
            try:
                metric_config = MetricConfig.objects.get(id=metric.get('id'))
            except MetricConfig.DoesNotExist:
                return error_response(message=f"Metric with id {metric.get('id')} not found", status=404)
            if metric_config.id not in existing_metrics:
                activity_metric = ActivityMetric.objects.create(
                    activity_data=activity_data,
                    metric=metric_config,
                    value=metric.get('value')
                )
            else:
                activity_metric = existing_metrics[metric_config.id]
                activity_metric.value = metric.get('value')
                activity_metric.save()
        
        return success_response(data=ActivityDataSerializer(activity_data).data, message="Activity data uploaded successfully", status=201)