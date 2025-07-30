from django.shortcuts import render
from rest_framework.views import APIView
from features.utils import authentication, permissions
from rest_framework import decorators
from rest_framework.permissions import AllowAny
from features.utils.response_wrapper import success_response, error_response
from . models import Season
from . serializer import SeasonSerializer, SeasonCreateSerializer
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
        serializer = SeasonCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                season = serializer.save(id=uuid4())
                return success_response(data=SeasonSerializer(season).data, message="Season created", status=status.HTTP_201_CREATED)
            except Exception as e:
                return error_response(message=str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return error_response(message=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

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
