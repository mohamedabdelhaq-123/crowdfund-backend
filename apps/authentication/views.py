from django.core import signing
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, LoginSerializer
from .utils import send_activation_email
from .models import User


class RegisterView(APIView):      # POST /auth/register/ — validates input, creates user, sends activation email
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()      # is_activated defaults to False in the model

        send_activation_email(user)      # send activation email with signed token

        return Response(
            {'message': 'Registration successful. Please check your email to activate your account.'},
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):      # GET /auth/activate/<token>/ — verifies signed token and activates the user
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user_pk = signing.loads(token, max_age=86400)      # max_age is 24 hours
        except signing.SignatureExpired:
            return Response(
                {'error': 'Activation link has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {'error': 'Invalid activation link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=user_pk)      # search for the user
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_activated:      # already activated
            return Response(
                {'message': 'Account is already activated. You can log in.'},
                status=status.HTTP_200_OK,
            )

        user.is_activated = True      # activate the account
        user.joined_at = timezone.now()
        user.save(update_fields=['is_activated', 'joined_at'])

        return Response(
            {'message': 'Account activated successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):      # POST /auth/login/ — validates credentials and sets JWT httpOnly cookies
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)      # generate token pair
        access = str(refresh.access_token)

        response = Response({'message': 'Login successful.'}, status=status.HTTP_200_OK)

        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=access,
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            value=str(refresh),
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )
        return response


class LogoutView(APIView):      # POST /auth/logout/ — blacklists refresh token and clears cookies
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])

        if not refresh_token:
            return Response({'error': 'No refresh token found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()      # add to blacklist DB table so it can't be reused
        except TokenError:
            pass      # token already expired or invalid, still clear cookies

        response = Response({'message': 'Logout successful.'}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'], path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'])
        return response


class ResendActivationView(APIView):      # POST /auth/resend-activation/ — sends new activation email with cooldown
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        generic_msg = {'message': 'If this email is registered, you will receive an activation link.'}

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(generic_msg, status=status.HTTP_200_OK)      # generic to prevent email enumeration

        if user.is_activated:
            return Response(generic_msg, status=status.HTTP_200_OK)      # don't reveal activation status

        cooldown = timedelta(minutes=2)
        if user.last_activation_sent and timezone.now() - user.last_activation_sent < cooldown:
            remaining = (user.last_activation_sent + cooldown - timezone.now()).seconds
            return Response(
                {'error': f'Please wait {remaining} seconds before requesting again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        send_activation_email(user)
        return Response(generic_msg, status=status.HTTP_200_OK)
