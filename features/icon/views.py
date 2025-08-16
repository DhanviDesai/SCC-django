from rest_framework import viewsets
from .models import Icon
from .serializers import IconSerializer
from features.utils.permissions import IsAdminRole
from features.utils.authentication import FirebaseAuthentication

class IconViewSet(viewsets.ModelViewSet):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAdminRole]
    queryset = Icon.objects.all()
    serializer_class = IconSerializer
