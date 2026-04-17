from django.urls import path
from .views import RegisterView, ActivateAccountView, LoginView, LogoutView, ResendActivationView, MeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('resend-activation/', ResendActivationView.as_view(), name='resend-activation'),
    path('me/', MeView.as_view(), name='me'),
]
