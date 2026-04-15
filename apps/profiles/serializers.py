from rest_framework import serializers
from apps.authentication.models import User


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'mobile_number',
            'profile_pic',
            'birthdate',
            'fb_profile',
            'country',
            'joined_at',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'joined_at', 'created_at']


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
