import random
from django.core.mail import send_mail
from django.conf import settings
from users.models import CustomUser, PasswordResetOTP
from django.utils.timezone import now
from datetime import timedelta


def generate_otp():
    return f"{random.randint(100000, 999999)}"


def send_otp_email(email, otp):
    subject = "Your OTP for Email Verification"
    message = f"Your OTP is {otp}. It is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])

def send_email_verification_email(user):
    subject = "Email Verification Confirmed from listaro"
    message = "Your email has been verified successfully."
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])

def send_reset_otp_email(email, otp):
    """Send the reset OTP to the user's email."""
    subject = "Password Reset OTP"
    message = f"Your OTP for resetting your password is: {otp}. It is valid for 10 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])

def create_and_send_password_reset_otp(user : CustomUser):
    """Generate and send OTP to the user."""
    otp_value = generate_otp()
    expires_at = now() + timedelta(minutes=10)  # OTP valid for 10 minutes

    # Create OTP entry
    PasswordResetOTP.objects.create(user=user, otp=otp_value, expires_at=expires_at)

    # Send OTP email
    send_reset_otp_email(user.email, otp_value)

def send_password_reset_confirmation_email(user : CustomUser):
    """Send an email to the user upon successful password reset.
    
    The email tells the user that their password has been reset successfully.
    """
    subject = "Password Reset Confirmation"
    message = "Your password has been reset successfully."
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])