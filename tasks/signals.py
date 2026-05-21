from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import UserTaskSubmission
from .services import credit_submission_reward
from django.conf import settings


@receiver(post_save, sender=UserTaskSubmission)
def handle_submission_post_save(sender, instance, created, **kwargs):
    # If newly created, do nothing (wait for admin)
    if created:
        return

    # If status became approved, attempt to credit (idempotent)
    if instance.status == instance.Status.APPROVED:
        try:
            credit_submission_reward(instance)
        except Exception:
            # Fail silently; admin actions should report errors
            pass
