from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from django.utils import timezone
import cloudinary

# Request → Serializer(data) → is_valid() triggers: field validators → validate() → model validators → save() triggers create() → Response

class RegisterSerializer(serializers.ModelSerializer):     # validates registration input

    uploaded_image_url = serializers.SerializerMethodField()
    confirm_password = serializers.CharField(write_only=True, required=True) #explicity field that will exist in the json

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
            'mobile_number',
            'profile_pic',
            'birthdate',
            'fb_profile',
            'country',
            "uploaded_image_url",
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'profile_pic': {'required': False, 'write_only': True},
            'birthdate': {'required': False},
            'fb_profile': {'required': False},
            'country': {'required': False},
        }

    def validate(self, attrs):         # ensure password and confirm_password match
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        return attrs
     
    def create(self, validated_data):    # remove confirm_password and use create_user() to hash the password
        validated_data.pop('confirm_password') #after validation remove the confirm field
        return User.objects.create_user(**validated_data) #create user by the key values
    

    def validate_birthdate(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Birthdate cannot be in the future.")
        return value
    
    def get_uploaded_image_url(self, obj):
        return cloudinary.CloudinaryImage(obj.profile_pic.name).build_url(
            width=300, 
            height=300, 
            crop="fill",    
            quality="auto",  
            fetch_format="auto", 
            secure=True
        )
  

    def create(self, validated_data):            # remove confirm_password and use create_user() to hash the password
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):      # validates login credentials and activation status
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):      # check credentials first, then activation status

        user = authenticate(email=attrs['email'], password=attrs['password'])

        if user is None:      # wrong email or password
            raise serializers.ValidationError({'error': 'Invalid email or password.'})

        if not user.is_activated:      # correct creds but not activated yet
            raise serializers.ValidationError({
                'error': 'Account is not activated. Please check your email.',
                'not_activated': True,      # flag so React frontend can show resend button
            })

        attrs['user'] = user      # attach user to validated_data for the view
        return attrs


class MeSerializer(serializers.ModelSerializer):      # read-only serializer for GET /auth/me/
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = fields
