from django.shortcuts import render
from rest_framework.views import APIView
from features.utils import authentication, permissions
from rest_framework import decorators
from rest_framework.permissions import AllowAny
from features.utils.response_wrapper import success_response, error_response
from . models import Season
from . serializer import SeasonSerializer
from uuid import uuid4
from rest_framework import status

# Create your views here.
class ListSeason(APIView):
    def get(self, request):
        queryset = Season.objects.all().order_by('-created_at')
        return success_response(SeasonSerializer(queryset, many=True).data, message="Season list fetched")

class IndexOperations(APIView):
    authentication_classes = [authentication.FirebaseAuthentication]
    permission_classes = [permissions.IsAdminRole]

    def post(self, request):
        name = request.data.get('season_name', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        if name is None:
            return error_response(message="season_name cannot be null or empty")
        try:
            season = Season.objects.create(id=uuid4(), name=name, start_date=start_date, end_date=end_date)
            return success_response(data=SeasonSerializer(season).data, message="Season cretaed", status=status.HTTP_201_CREATED)
        except Exception as e:
            return error_response(message=str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    @decorators.permission_classes([AllowAny])
    def get(self, request, season_id):
        if season_id is None:
            queryset = Season.objects.all()
        else:
            queryset = Season.objects.filter(id=season_id)
        return success_response(data=SeasonSerializer(queryset, many=True).data, message="Season list fetched")

    def put(self, request, season_id):
        pass

    def delete(self, request, season_id):
        pass
