from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationCreateRetrieve,DonationList




urlpatterns = [
    path("",DonationList.as_view(),name="user-donations"),
    path("<int:project_id>/",DonationCreateRetrieve.as_view(),name="user-project-donations")
]