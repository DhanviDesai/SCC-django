from django.urls import path

from . import views

urlpatterns = [
    path("list", views.CompanyListView.as_view()),
    path("presigned-url", views.GetPresignedUrl().as_view(), name="get presigned url for image upload to S3 bucket"),
    path("<slug:company_id>", views.IndexOperations.as_view(), name="list_company"),
    
    # path("<slug:company_id>", views.CompanyOperations.as_view(), name="Individual company operations"),
]