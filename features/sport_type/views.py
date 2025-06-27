from django.shortcuts import render
from rest_framework.views import APIView
from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import IsAdminRole
from rest_framework import decorators
from rest_framework.permissions import AllowAny
from features.utils.response_wrapper import success_response

from . models import SportType
from .serializers import SportTypeSerializer

# Create your views here.
class ListSportType(APIView):
    def get(self, request):
        queryset = SportType.objects.all()
        return success_response(data=SportTypeSerializer(queryset, many=True).data, message="Sport type list fetched")

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        return success_response()
    
    def put(self, request, type_id):
        pass

    def delete(self, request, type_id):
        pass

    def get(self, request, type_id=None):
        queryset = SportType.objects.filter(id=type_id)
        return success_response(data=SportTypeSerializer(queryset).data, message="Sport type fetched")
            