from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

MEDIA_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "mp4", "webm", "mov"]

class Task(models.Model):
    MEDIA_TYPE_CHOICES = (("image", "Image"), ("video", "Video"))

    title = models.CharField(max_length=255)
    description = models.TextField()
    reward = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(default=30, help_text="Task duration in minutes")
    media = models.URLField(blank=True, null=True, default='')
    media_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video')], default='image')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Plan(models.Model):
    PLAN_LEVEL_CHOICES = (
        (1, "Plan 1"),
        (2, "Plan 2"),
        (3, "Plan 3"),
        (4, "Plan 4"),
    )
    
    # Fixed amounts for each plan level
    PLAN_AMOUNTS = {
        1: 20.00,   # Plan 1 → $20
        2: 50.00,   # Plan 2 → $50
        3: 80.00,   # Plan 3 → $80
        4: 120.00,  # Plan 4 → $120
    }
    
    # Reward multipliers for each plan level
    PLAN_MULTIPLIERS = {
        1: 1.0,
        2: 1.5,
        3: 2.0,
        4: 2.5,
    }
    
    # Daily earning limits for each plan level
    PLAN_DAILY_LIMITS = {
        1: 50.00,
        2: 100.00,
        3: 200.00,
        4: 350.00,
    }
    
    # Max tasks per day for each plan level
    PLAN_MAX_TASKS = {
        1: 20,
        2: 40,
        3: 60,
        4: 100,
    }
    
    plan_level = models.PositiveSmallIntegerField(
        choices=PLAN_LEVEL_CHOICES,
        unique=True,
        null=True,
        blank=True,
        help_text="Plan level (1-4) with fixed amounts"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Required deposit amount to activate this plan"
    )
    reward_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=1.0,
        null=True,
        blank=True,
        help_text="Task reward multiplier"
    )
    daily_earning_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=50.0,
        null=True,
        blank=True,
        help_text="Maximum daily earning limit"
    )
    max_tasks_per_day = models.PositiveIntegerField(
        default=20,
        null=True,
        blank=True,
        help_text="Maximum tasks per day"
    )
    duration_days = models.PositiveSmallIntegerField(default=30, help_text="Plan duration in days")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['plan_level']

    def __str__(self):
        if self.plan_level:
            return f"Plan {self.plan_level} - ${self.amount}"
        return f"{self.title} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Auto-set amount, multiplier, and limits based on plan level if not provided
        if self.plan_level in self.PLAN_AMOUNTS:
            if not self.amount or self.amount == 0:
                self.amount = self.PLAN_AMOUNTS[self.plan_level]
            if not self.reward_multiplier or self.reward_multiplier == 1.0:
                self.reward_multiplier = self.PLAN_MULTIPLIERS[self.plan_level]
            if not self.daily_earning_limit or self.daily_earning_limit == 50.0:
                self.daily_earning_limit = self.PLAN_DAILY_LIMITS[self.plan_level]
            if not self.max_tasks_per_day or self.max_tasks_per_day == 20:
                self.max_tasks_per_day = self.PLAN_MAX_TASKS[self.plan_level]
        super().save(*args, **kwargs)

class UserTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="completed_tasks")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "task", "completed_date")
        ordering = ("-completed_at",)
        indexes = [
            models.Index(fields=['user', 'completed_date']),
            models.Index(fields=['task', 'completed_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.task.title}"

class UserPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plans")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="subscriptions")
    joined_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Plan expiration date")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = ("user", "plan")
        ordering = ("-joined_at",)
        indexes = [
            models.Index(fields=['user', 'plan']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.plan.title}"
    
    def is_expired(self):
        """Check if the plan subscription has expired"""
        if not self.is_active:
            return True
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.is_expired():
            return 0
        if self.expires_at:
            from django.utils import timezone
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return None

class SystemSettings(models.Model):
    """Global system settings for dynamic configuration"""
    telegram_link = models.URLField(blank=True, null=True, help_text="Telegram group/channel link")
    whatsapp_link = models.URLField(blank=True, null=True, help_text="WhatsApp group link")
    support_phone = models.CharField(max_length=50, blank=True, null=True, help_text="Support phone or WhatsApp number")
    support_email = models.EmailField(blank=True, null=True, help_text="Support email address")
    facebook_link = models.URLField(blank=True, null=True, help_text="Facebook page link")
    instagram_link = models.URLField(blank=True, null=True, help_text="Instagram profile link")
    announcement_banner = models.TextField(blank=True, null=True, help_text="Announcement banner text")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "System Settings"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get the singleton settings instance, create if doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
