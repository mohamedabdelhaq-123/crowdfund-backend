from django.urls import path
from .views import RegisterView, ActivateAccountView, LoginView, LogoutView, ResendActivationView, MeView, CookieTokenRefreshView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('resend-activation/', ResendActivationView.as_view(), name='resend-activation'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
]
