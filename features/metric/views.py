from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.authentication import FirebaseAuthentication
from features.utils.response_wrapper import success_response, error_response
from features.users.models import User
from datetime import datetime

from .models import StepMetric
from .serializers import StepMetricSerializer

# Create your views here.


class StepMetricView(APIView):
    authentication_classes = [FirebaseAuthentication]
    def post(self, request):
        date = request.data.get('date')
        if date is None:
            return error_response(message="Date cannot be null")
        count = request.data.get('count')
        if count is None:
            return error_response(message="Count cannot be null")

        # Get the user
        uid = request.auth.get('user_id')
        user = User.objects.get(firebase_uid=uid)
        

        # Insert the count in step metric table for this user and the date.
        dt_object = datetime.fromisoformat(date.replace('Z', '+00:00'))
        date_object = dt_object.date()
        step_metric, created = StepMetric.objects.update_or_create(
            user=user,
            date=date_object,
            defaults={'count': count}
        )
        return success_response(data=StepMetricSerializer(step_metric).data, message="Metric updated successfully")
