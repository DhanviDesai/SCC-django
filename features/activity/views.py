from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
import logging

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from features.users.models import User
from features.utils.response_wrapper import success_response, error_response
from features.metric.models import MetricConfig

from . models import ActivityConfig, ActivityMetric, ActivityData
from .serializers import ActivityConfigReadSerializer, ActivityConfigWriteSerializer, ActivityDataSerializer

logger = logging.getLogger(__name__)

# Create your views here.
class ActivityConfigViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    queryset = ActivityConfig.objects.all()

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
        # Placeholder for future implementation
        # Here, I get the request.data containing activity_id, start and end date with value for each metrics for this activity
        # Get the user
        user = User.objects.get(firebase_uid=request.auth.get('user_id'))
        # Check whether the activity exists
        try:
            activity = ActivityConfig.objects.get(id=request.data.get('activity'))
        except ActivityConfig.DoesNotExist:
            return error_response(message="Activity not found", status=404)
        logger.info("Got activity")
        # Create rows for ActivityMetrics
        activity_metrics = []
        print(request.data.get('metrics'))
        # Create a new ActivityData instance
        activity_data = ActivityData.objects.create(
            user=request.user,
            activity=activity,
            start_datetime=request.data.get('start_datetime'),
            end_datetime=request.data.get('end_datetime')
        )
        for metric_data in request.data.get('metrics'):
            # Assuming metric is a dict with 'metric_id' and 'value'
            try:
                metric = MetricConfig.objects.get(id=metric_data.get('id'))
            except MetricConfig.DoesNotExist:
                return error_response(message="Metric not found", status=404)
            activity_metric = ActivityMetric.objects.create(activity_data=activity_data, metric=metric, value=metric_data.get('value'))
        return success_response(data=ActivityDataSerializer(activity_data).data, message="Data inserted successfully")