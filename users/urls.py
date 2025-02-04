from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, VerifyOTPView, ResendOTPView,
    RequestPasswordResetView, ResetPasswordView, UserListView, UserDetailView, UserInfoView,
    UserUpdateView, UserDeleteView, GoogleAuthView,
)

from rest_framework_simplejwt.views import TokenVerifyView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    
    path('users/', UserListView.as_view(), name='user-list'),
    path('userInfo/', UserInfoView.as_view(), name='user-info'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),

    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]