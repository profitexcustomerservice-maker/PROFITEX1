from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_admin = models.BooleanField(default=False, db_index=True)
    current_plan_level = models.PositiveSmallIntegerField(default=0, db_index=True, help_text="Current plan level (0=None, 1-4)")
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)
    referral_code = models.CharField(max_length=20, unique=True, db_index=True, null=True, blank=True, help_text="Unique referral code for this user")
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals', help_text="User who referred this user")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(null=True, blank=True)
    last_rewarded_at = models.DateTimeField(null=True, blank=True)


    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def has_active_plan(self):
        """Check if user has an active, non-expired plan"""
        return self.plans.filter(is_active=True).exclude(
            expires_at__isnull=False,
            expires_at__lt=timezone.now()
        ).exists()
    
    def get_active_plan(self):
        """Get the user's active plan (if any)"""
        from django.utils import timezone
        active_plans = self.plans.filter(is_active=True).exclude(
            expires_at__isnull=False,
            expires_at__lt=timezone.now()
        )
        return active_plans.first() if active_plans.exists() else None
    
    def get_plan_level(self):
        """Get the highest active plan level"""
        active_plan = self.get_active_plan()
        return active_plan.plan.plan_level if active_plan else 0


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_verified', 'created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"
    
    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at < timezone.now() - timedelta(minutes=5)


class SocialLink(models.Model):
    """Social media links for the platform"""
    name = models.CharField(max_length=50)  # Telegram, Facebook, etc.
    url = models.URLField()
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome icon class (fa-telegram, fa-facebook)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)  # For sorting
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Social Link"
        verbose_name_plural = "Social Links"
    
    def __str__(self):
        return self.name


class Referral(models.Model):
    """Track referral relationships and rewards"""
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrer_relationships')
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_relationships')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Reward given to referrer")
    is_active = models.BooleanField(default=True, help_text="Is the referral active/valid")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer', 'is_active']),
            models.Index(fields=['referred_user']),
        ]
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
    
    def __str__(self):
        return f"{self.referrer.email} referred {self.referred_user.email}"
