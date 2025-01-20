from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password']

    def validate(self, data):
        # Check if the email is already registered
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


    def validate(self, data):
        # Authenticate the user
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        user = CustomUser.objects.filter(email=email).first()
        # Ensure email is verified
        if not user.email_verified:
            raise serializers.ValidationError("Email is not verified.")

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details (read-only)
    """
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'credits', 'is_active', 
            'is_staff', 'email_verified', 'picture', 'provider'
        ]
        read_only_fields = ['id', 'email', 'is_active', 'is_staff', 'email_verified', 'provider']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'picture']

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
