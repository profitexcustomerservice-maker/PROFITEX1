from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class TaskType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        UPLOAD = 'upload', 'Upload'
        REVIEW = 'review', 'Review'
        VIDEO = 'video', 'Video'
        AD_LINK = 'ad_link', 'Ad Link'
        IMAGE_REVIEW = 'image_review', 'Image Review'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.QUIZ)
    
    # Media fields for images, links, and videos
    media = models.ImageField(upload_to='task_media/', blank=True, null=True, help_text='Image or thumbnail')
    media_type = models.CharField(max_length=20, blank=True, choices=[
        ('image', 'Image'),
        ('video', 'Video'),
        ('link', 'External Link'),
    ])
    
    # Link/URL field for ad links or external tasks
    ad_url = models.URLField(blank=True, null=True, help_text='Link to external ad or website')
    
    # Duration tracking for link/video viewing
    required_duration = models.PositiveIntegerField(default=0, help_text='Required seconds to spend on task (0 = no minimum)')
    
    # Survey/form data (JSON)
    survey_data = models.JSONField(default=dict, blank=True, help_text='Survey questions and options')
    
    # Premium tier requirement
    premium_only = models.PositiveSmallIntegerField(default=0, help_text='Minimum plan level (0=all, 1-4=plan level)')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_type', 'is_active']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Task({self.title})"
    
    def get_thumbnail_url(self):
        """Return thumbnail URL (media or generated from link)"""
        if self.media:
            return self.media.url
        return None


class UserTaskSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_submissions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_data = models.TextField(blank=True)  # could store file path, url or text
    
    # Timer tracking for link/video viewing
    time_spent = models.PositiveIntegerField(default=0, help_text='Seconds spent on task')
    timer_started_at = models.DateTimeField(null=True, blank=True, help_text='When user started the timer')
    timer_completed_at = models.DateTimeField(null=True, blank=True, help_text='When user completed the timer')
    link_opened_at = models.DateTimeField(null=True, blank=True, help_text='When user opened the external link')
    
    admin_comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_submissions')

    class Meta:
        ordering = ('-submitted_at',)
        indexes = [
            models.Index(fields=['user', 'task']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Submission(user={self.user_id}, task={self.task_id}, status={self.status})"
    
    def is_minimum_duration_met(self):
        """Check if user met the minimum required duration"""
        if not self.task.required_duration:
            return True  # No minimum required
        return self.time_spent >= self.task.required_duration
