from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import uuid4
from rest_framework.permissions import IsAuthenticated
import boto3
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import HasRole, IsAdminRole
from features.utils.storage import generate_presigned_url
from features.utils.response_wrapper import success_response, error_response
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics

from .models import Company, CompanyStatus
from .serializers import CompanySerializer

# Create your views here.
class CompanyPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class CompanyListView(generics.ListAPIView):
    queryset = Company.objects.all().order_by('company_name')
    serializer_class = CompanySerializer
    pagination_class = CompanyPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company_name']
    search_fields = ['^company_name']

class AddCompany(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        company_logo_link = request.data.get('company_logo_link')
        company_name = request.data.get('company_name')
        company = Company.objects.create(company_id=str(uuid4()), company_name=company_name, company_logo=company_logo_link)
        return success_response(data=CompanySerializer(company).data, message="Company added")

class IndexOperations(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]

    def get(self, request, id=None):
        if id is None:
            queryset = Company.objects.all().order_by('company_name')
        else:
            queryset = Company.objects.filter(id=id)
        return success_response(data=CompanySerializer(queryset, many=True).data, message="Compnay fetched")

    def put(self, request, id):
        company_name = request.data.get('company_name')
        company_logo_link = request.data.get('company_logo_link')
        company = Company.objects.get(id=id)
        if company_name is not None:
            company.company_name = company_name
        if company_logo_link is not None:
            company.company_logo = company_logo_link
        company.save()

    def delete(self, request, id):
        company = Company.objects.get(id=id)
        company.status = CompanyStatus.DELETED
        company.save()
        return success_response(data=CompanySerializer(company).data, message="Company deleted")

class GetPresignedUrl(APIView):
    def options(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_200_OK)

    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def get(self, request):
        file_name = request.GET.get("filename")
        file_type = request.GET.get("filetype")

        try:
            presigned_url, public_url = generate_presigned_url(f"companies/{file_name}", file_type)
            data = {
                "presigned_url": presigned_url,
                "public_url": public_url
            }
            return success_response(data=data, message="Presigned url generated")
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))