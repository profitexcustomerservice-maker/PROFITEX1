from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class TaskType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        UPLOAD = 'upload', 'Upload'
        REVIEW = 'review', 'Review'
        VIDEO = 'video', 'Video'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.QUIZ)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task({self.title})"


class UserTaskSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_submissions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_data = models.TextField(blank=True)  # could store file path, url or text
    admin_comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_submissions')

    class Meta:
        ordering = ('-submitted_at',)

    def __str__(self):
        return f"Submission(user={self.user_id}, task={self.task_id}, status={self.status})"
