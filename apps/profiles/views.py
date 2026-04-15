from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .serializers import ProfileSerializer, DeleteAccountSerializer
from apps.authentication.models import User


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['password']):
            return Response(
                {'password': 'incorrect password'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(
            {'detail': 'account deleted successfully'},
            status=status.HTTP_204_NO_CONTENT,
        )


class PublicProfileView(APIView):
    permission_classes = []

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'user not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
