import requests
from datetime import timedelta

from django.utils.timezone import now

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import CustomUser, OTP, PasswordResetOTP
from .utils import generate_otp, send_otp_email, send_email_verification_email, create_and_send_password_reset_otp, send_password_reset_confirmation_email

from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView

from django_ratelimit.decorators import ratelimit 
from django.utils.decorators import method_decorator

from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated

from rest_framework.exceptions import PermissionDenied


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        get_user = CustomUser.objects.get(email=user.email)
        otp_value = generate_otp()
        otp_expiry = now() + timedelta(minutes=10)
        OTP.objects.filter(user=get_user, purpose="email_verification").delete()  
        OTP.objects.create(user=get_user, otp=otp_value, purpose="email_verification", expires_at=otp_expiry)
        otp = OTP.objects.filter(user=get_user, otp=otp_value, purpose="email_verification").first()
        send_otp_email(email=get_user.email , otp=otp.otp)
       

        if user.email_verified:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "user": serializer.data,
                    "refresh": refresh_token,
                    "access": access_token,
                },
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            return Response({"message": "User Created, Please verify your email."}, status=status.HTTP_201_CREATED)
        

class LoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

class UserInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not request.user.is_authenticated:
            return Response({"error": "User not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
class GoogleAuthView(APIView):
    permission_classes = []

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Load the strategy and backend
            # strategy = load_strategy(request)
            # backend = load_backend(strategy=strategy, name='google-oauth2', redirect_uri=None)

            # Authenticate the user with the Google backend
             # Attempt to fetch user data using the backend
            user_data = None
            try:
                headers = {"Authorization": f"Bearer {id_token}"}
                response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
                user_data = response.json()
                print(user_data)
                print(response)
            except Exception as e:
                print(f"Error retrieving user data from Google: {str(e)}")
                return Response({"error": "Failed to retrieve user data from Google."}, status=status.HTTP_400_BAD_REQUEST)
            
            user_email = user_data.get("email")
            user_name = user_data.get("name", "")
            

            if not user_email:
                return Response({"error": "Google response did not contain an email."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user already exists
            user, created = CustomUser.objects.get_or_create(
                email=user_email,
                defaults={
                    "username": user_name,
                    "provider": "google",
                    "email_verified": True,  # Mark as verified since it's from Google
                }
            )

            if not created:  # Existing user
                # Ensure provider is updated if necessary
                if user.provider != "google":
                    user.provider = "google"
                    user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "email": user.email,
                    "username": user.username,
                    "email_verified": user.email_verified,
                    "provider": user.provider,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        email = request.data.get("email")
        otp_value = request.data.get("otp")

        if not email or not otp_value:
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            if user.email_verified:
                return Response({"error": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
            otp = OTP.objects.filter(user=user, otp=otp_value, purpose="email_verification").first()

            if not otp or not otp.is_valid():
                return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

            user.email_verified = True
            user.save()
            otp.delete()

            send_email_verification_email(user)
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "CustomUser does not exist."}, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    # @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    permission_classes = (AllowAny,)
    def post(self, request):
        email = request.data.get("email")
        print(email)

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            otp_value = generate_otp()
            otp_expiry = now() + timedelta(minutes=10)

            OTP.objects.filter(user=user, purpose="email_verification").delete()  # Remove old OTPs
            OTP.objects.create(user=user, otp=otp_value, purpose="email_verification", expires_at=otp_expiry)

            send_otp_email(email, otp_value)
            return Response({"message": "OTP resent successfully."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "CustomUser does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            create_and_send_password_reset_otp(user)
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "CustomUser with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
class ResetPasswordView(APIView):
    @method_decorator(ratelimit(key="ip", rate="5/m", block=True))
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not email or not otp or not new_password:
            return Response({"error": "Email, OTP, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            reset_otp = PasswordResetOTP.objects.filter(user=user, otp=otp).first()

            if not reset_otp:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            if not reset_otp.is_valid():
                return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the password
            user.set_password(new_password)
            user.save()

            # Delete the OTP after successful reset
            reset_otp.delete()
            send_password_reset_confirmation_email(user)
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "CustomUser with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        


class UserListView(APIView):
    """
    Retrieve a list of users.
    - Superusers can see all users.
    - Regular users can only see their own account.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_superuser:
            users = CustomUser.objects.all()
        else:
            users = CustomUser.objects.filter(id=request.user.id)
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    """
    Retrieve details of a specific user.
    - Only superusers or the user themselves can view this.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if request.user.is_superuser or request.user.id == user.id:
                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            raise PermissionDenied("You do not have permission to view this user.")
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class UserUpdateView(APIView):
    """
    Update a user's details.
    - Only superusers or the user themselves can perform this.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if request.user.is_superuser or request.user.id == user.id:
                serializer = UserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            raise PermissionDenied("You do not have permission to update this user.")
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class UserDeleteView(APIView):
    """
    Delete a user account.
    - Only superusers or the user themselves can perform this.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
            if request.user.is_superuser or request.user.id == user.id:
                user.delete()
                return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            raise PermissionDenied("You do not have permission to delete this user.")
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
