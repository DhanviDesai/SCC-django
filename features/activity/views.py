from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
import logging
import json
import pytz

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
    queryset = ActivityConfig.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminRole]
        else:
            self.permission_classes = []
        return super().get_permissions()

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

        activities = []
        
        if isinstance(request.data, list):
            activities = request.data
        else:
            activities.append(request.data)
        
        logger.info(activities)

        # Check whether the activity exists
        for request_activity in activities:
            try:
                activity = ActivityConfig.objects.get(id=request_activity.get('activity'))
            except ActivityConfig.DoesNotExist:
                return error_response(message="Activity not found", status=404)
            
            # Clients would always update the data in hourly chunks. Data would be stored in DB in UTC format
            if not request_activity.get('start_datetime'):
                return error_response(message="start_datetime is required", status=400)
            if not request_activity.get('end_datetime'):
                return error_response(message="end_datetime is required", status=400)
            if not request_activity.get('metrics'):
                return error_response(message="metrics are required", status=400)
            
            try:
                start_datetime = datetime.fromisoformat(request_activity.get('start_datetime'))
                end_datetime = datetime.fromisoformat(request_activity.get('end_datetime'))
                if start_datetime >= end_datetime:
                    return error_response(message="start_datetime must be before end_datetime", status=400)
            except ValueError:
                return error_response(message="Invalid date format. Use ISO 8601 format.", status=400)
            
            
            if (end_datetime - start_datetime).total_seconds() <= 0:
                return error_response(message="end_datetime must be after start_datetime", status=400)
            
            # Check whether the metrics are valid for the activity
            valid_metric_ids = set(activity.metrics.values_list('id', flat=True))
            for metric in request_activity.get('metrics', []):
                if metric.get('id') not in valid_metric_ids:
                    return error_response(message=f"Metric with id {metric.get('id')} is not valid for this activity", status=400)
            
            # This works well for old data, like 2025-09-01T10:00:00 to 2025-09-01T11:00:00
            # How to handle for data upload like 2025-09-01T10:00:00 to 2025-09-01T10:37:00 and another upload with 2025-09-01T10:00:00 to 2025-09-01T11:00:00

            activity_data, created = ActivityData.objects.get_or_create(
                user=user,
                activity=activity,
                start_datetime=start_datetime,
                defaults={'end_datetime': end_datetime}
            )
            if not created:
                activity_data.end_datetime = end_datetime
                activity_data.save()
            
            # Get all the ActivityMetric objects for the activity_data
            existing_metrics = {am.metric.id: am for am in ActivityMetric.objects.filter(activity_data=activity_data)}
            
            # Update the ActivityMetric object values from the metrics in the request
            for metric in request_activity.get('metrics', []):
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
        
        return success_response(data={}, message="Activity data uploaded successfully", status=201)

class ActivityDataDeleteView(APIView):
    authentication_classes = [FirebaseAuthentication]

    def delete(self, request):
        user = User.objects.get(firebase_uid=request.auth.get('user_id'))
        ActivityData.objects.filter(user=user).delete()
        return success_response(data={}, message="Activity data deleted successfully", status=200)