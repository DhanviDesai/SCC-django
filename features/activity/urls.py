from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'config', views.ActivityConfigViewSet, basename='activity-config')

urlpatterns = [
    path('', include(router.urls)),
    path('data', views.ActivityDataPostView.as_view(), name='activity-data-post'),
    path('data/<int:activity_id>', views.ActivityDataListView.as_view(), name='activity-data-upload')
]