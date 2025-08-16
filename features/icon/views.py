import uuid
import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Icon
from .serializers import IconSerializer
from features.utils.permissions import IsAdminRole
from features.utils.authentication import FirebaseAuthentication
from features.utils.storage import generate_presigned_url
from features.utils.response_wrapper import success_response, error_response

class IconViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    queryset = Icon.objects.all()
    serializer_class = IconSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        name = serializer.validated_data.get('name', file.name)

        file_name = f"icons/{uuid.uuid4()}-{file.name}"
        presigned_url, public_url = generate_presigned_url(file_name, file.content_type)

        try:
            response = requests.put(presigned_url, data=file.read())
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return error_response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        icon = Icon.objects.create(name=name, url=public_url)
        return success_response(IconSerializer(icon).data, "Icon uploaded successfully.", status=status.HTTP_201_CREATED)
