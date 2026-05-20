from django.contrib import admin
from .models import Task, UserTaskSubmission
from .services import credit_submission_reward
from django.contrib import messages


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'reward_amount', 'is_active', 'created_at')
    list_filter = ('task_type', 'is_active')
    search_fields = ('title',)


@admin.register(UserTaskSubmission)
class UserTaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('user__email', 'task__title')
    actions = ['approve_submissions', 'reject_submissions']

    def approve_submissions(self, request, queryset):
        approved = 0
        for submission in queryset.select_for_update():
            if submission.status == submission.Status.APPROVED:
                continue
            try:
                tx = credit_submission_reward(submission, reviewer=request.user)
                approved += 1 if tx else 0
            except Exception as e:
                self.message_user(request, f"Error approving {submission.id}: {e}", level=messages.ERROR)

        self.message_user(request, f"Approved {approved} submissions and credited rewards.")
    approve_submissions.short_description = "Approve selected submissions and credit rewards"

    def reject_submissions(self, request, queryset):
        updated = queryset.exclude(status=UserTaskSubmission.Status.REJECTED).update(status=UserTaskSubmission.Status.REJECTED, reviewed_at=None)
        self.message_user(request, f"Marked {updated} submissions as rejected.")
    reject_submissions.short_description = "Reject selected submissions"
