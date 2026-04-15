from django.urls import path
from .views import ProfileView, PublicProfileView, MyProjectsView

urlpatterns = [
    path('me/', ProfileView.as_view(), name='profile-me'),
    path('me/projects/', MyProjectsView.as_view(), name='my-projects'),
    path('<int:id>/', PublicProfileView.as_view(), name='public-profile'),
]
