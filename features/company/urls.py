from django.urls import path

from . import views

urlpatterns = [
    path("add", views.AddCompany().as_view(), name="create_company"),
    path("list", views.ListCompany().as_view(), name="list_company"),
    path("presigned-url", views.GetPresignedUrl().as_view(), name="get presigned url for image upload to S3 bucket")
]