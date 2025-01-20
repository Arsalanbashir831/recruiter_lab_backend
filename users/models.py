from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.timezone import now
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not username:
            raise ValueError('Superuser must have a username.')
        return self.create_user(email, username=username, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=80)
    credits = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    # listings_limit = models.IntegerField(default=0)
    # keywords_limit = models.IntegerField(default=0)
    picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    objects = CustomUserManager()
    provider = models.CharField(max_length=50, blank=True, null=True, default='email')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email



class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="otps")
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, default="email_verification")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return now() < self.expires_at
    
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reset_otps")
    otp = models.CharField(max_length=6)  # OTP is a 6-digit numeric code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        """Check if the OTP is still valid."""
        return self.expires_at > now()
    

# class SubscriptionPlan(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     description=models.CharField(max_length=400, default='')
#     billing_cycle = models.CharField(max_length=10, default='month')  # 'month' or 'year'
#     features = models.JSONField()  # Store features as a JSON object
#     stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
#     stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

#     def __str__(self):
#         return self.name


# class Subscription(models.Model):
#     STATUS_CHOICES = [
#         ('active', 'Active'),
#         ('expired', 'Expired'),
#         ('cancelled', 'Cancelled'),
#         ('inactive', 'Inactive'),
#     ]
#     user = models.ForeignKey(
#         CustomUser, on_delete=models.CASCADE, related_name='subscriptions'
#     )
#     plan = models.ForeignKey(
#         SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions',
#         null=True,
#         blank=True,
#     )
#     stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
#     used_listings = models.IntegerField(default=0)  # Tracks used listings
#     used_keywords = models.IntegerField(default=0)  # Tracks used keywords
#     renewal_date = models.DateTimeField(default=now)  # Date when limits are next renewed
#     start_date = models.DateTimeField(auto_now_add=True)
#     end_date = models.DateTimeField()
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

#     def __str__(self):
#         return f"{self.user.email} - {self.plan.name} ({self.status})"
    
#     def renew_limits(self):
#         """Renew limits if renewal date has passed and subscription is still active."""
#         if self.status == 'active' and now() >= self.renewal_date and now() < self.end_date:
#             # Reset listings and keyword usage
#             self.used_listings = 0
#             self.used_keywords = 0
#             # Update renewal date to one month ahead
#             self.renewal_date = self.renewal_date + timedelta(days=30)
#             self.save()
    
#     def zero_listings(self):
#         self.used_listings = 0
#         self.save()

#     def zero_keywords(self):
#         self.used_keywords = 0
#         self.save()
        
#     def has_time_left(self):
#         """Check if subscription is still within the active period."""
#         return now() < self.end_date

#     def is_active(self):
#         return self.status == 'active' and now() < self.end_date

#     def renew(self):
#         self.start_date = now()
#         self.end_date = now() + timedelta(days=30)  # Default renewal for 1 month
#         self.status = 'active'
#         self.save()

    

from .contact_helpers import send_contact_email_to_admin, send_query_response_email_to_user, send_confirmation_email_to_user
class ContactForm(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    resolution = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    def __str__(self):
        return f"{self.name} - {self.email}"
    

    def send_email_to_admin(self):
        try: 
            print(self.email, self.name, self.message)
            if not self.email or not self.name or not self.message:
                raise ValueError("Email, name, and message are required.")
            send_contact_email_to_admin(self.name, self.email, self.message)

        except Exception as e:
            print(f"Error sending email: {e}")

    def send_confirmation(self):
        try:
            if not self.email:
                raise ValueError("Email is required.")
            if not self.id:
                raise ValueError("ID is required.")
            if not self.name:
                raise ValueError("Name is required.")
            send_confirmation_email_to_user(self.name, self.email, self.id)

        except Exception as e:
            print(f"Error sending email: {e}")

    def send_response(self):
        try:
            if not self.email:
                raise ValueError("Email is required.")
            if not self.resolution:
                raise ValueError("Resolution is required.")
            send_query_response_email_to_user(self.email, self.resolution)
            self.status = 'resolved'
            self.save()

        except Exception as e:
            print(f"Error sending email: {e}")

