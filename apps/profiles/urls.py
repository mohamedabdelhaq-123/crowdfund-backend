from django.urls import path
from .views import ProfileView, PublicProfileView

urlpatterns = [
    path('me/', ProfileView.as_view(), name='profile-me'),
    path('<int:id>/', PublicProfileView.as_view(), name='public-profile'),
]
