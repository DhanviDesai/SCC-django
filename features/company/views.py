from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import uuid4
from rest_framework.permissions import IsAuthenticated
import boto3
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from features.utils.authentication import FirebaseAuthentication
from features.utils.permissions import HasRole, IsAdminRole
from features.utils.response_wrapper import success_response, error_response

from .models import Company
from .serializers import CompanySerializer

# Create your views here.
class ListCompany(APIView):
    authentication_classes = [FirebaseAuthentication]
    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return success_response(data=serializer.data, message="Company list fetched", status=status.HTTP_200_OK)

class AddCompany(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def post(self, request):
        company_logo_link = request.data.get('company_logo_link')
        company_name = request.data.get('company_name')
        company = Company.objects.create(company_id=str(uuid4()), company_name=company_name, company_logo=company_logo_link)
        company.save()
        return success_response(data=CompanySerializer(company).data, message="Company Added", status=status.HTTP_201_CREATED)

class GetPresignedUrl(APIView):
    def options(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_200_OK)

    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    def get(self, request):
        file_name = request.GET.get("filename")
        file_type = request.GET.get("filetype")

        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        try:
            presigned_url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "Key": file_name,
                    "ContentType": file_type
                },
                ExpiresIn=60
            )
            public_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_name}"
            data = {
                "presigned_url": presigned_url,
                "public_url": public_url
            }
            return success_response(data=data, message="Presigned url generated")
        except Exception as e:
            return error_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))