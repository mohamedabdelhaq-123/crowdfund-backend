from django.urls import path
from .views import ProfileView, PublicProfileView, MyProjectsView, MyDonationsView

urlpatterns = [
    path('me/', ProfileView.as_view(), name='profile-me'),
    path('me/projects/', MyProjectsView.as_view(), name='my-projects'),
    path('me/donations/', MyDonationsView.as_view(), name='my-donations'),
    path('<int:id>/', PublicProfileView.as_view(), name='public-profile'),
]
