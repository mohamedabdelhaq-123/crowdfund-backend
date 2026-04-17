from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


# custom auth class that reads the JWT access token from an httpOnly cookies instead of the Authorization header
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE']) # search for token in cookies

        if raw_token is None:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
