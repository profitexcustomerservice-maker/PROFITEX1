from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from .models import UserTask
from wallet.models import Transaction, Wallet
from notifications.models import Notification

@receiver(post_save, sender=UserTask)
def reward_user_task_completion(sender, instance, created, **kwargs):
    if not created:
        return
    reward_amount = instance.task.reward
    if reward_amount <= 0:
        return
    with transaction.atomic():
        wallet = instance.user.wallet
        wallet.add_balance(
            amount=reward_amount,
            transaction_type=Transaction.TransactionType.TASK_REWARD,
            reference=f"task-{instance.task.id}-{instance.id}"
        )
        Notification.objects.create(
            user=instance.user,
            title="Task completed",
            message=f"Your wallet was credited with ${reward_amount} for task '{instance.task.title}'.",
        )
