from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from wallet.models import Wallet
from notifications.models import Notification
from .models import User

@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        # Send welcome notification
        try:
            Notification.objects.create(
                user=instance,
                title="Welcome to Profitex",
                message="Your account has been created successfully. Start earning by completing tasks!",
            )
        except Exception:
            pass

@receiver(post_save, sender=User)
def update_last_active_for_login(sender, instance, **kwargs):
    if instance.last_active is None:
        instance.last_active = timezone.now()
        instance.save(update_fields=["last_active"])
