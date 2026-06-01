from decimal import Decimal

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from wallet.models import Wallet, Transaction
from notifications.models import Notification
from .models import User, Referral
import uuid


def generate_unique_referral_code():
    """Generate a unique referral code"""
    while True:
        code = str(uuid.uuid4())[:8].upper()
        if not User.objects.filter(referral_code=code).exists():
            return code


@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if not instance.referral_code:
        instance.referral_code = generate_unique_referral_code()
        instance.save(update_fields=['referral_code'])

    if created:
        # Use get_or_create to prevent duplicate key errors
        Wallet.objects.get_or_create(user=instance)
        # Send welcome notification
        try:
            Notification.objects.create(
                user=instance,
                title="Welcome to Profitex",
                message="Your account has been created successfully. Start earning by completing tasks!",
            )
        except Exception:
            pass


def apply_referral_reward_to_referrer(referred_user):
    """Credit the referrer when a referred user earns their first qualifying deposit or plan activation."""
    if not referred_user or not referred_user.referred_by:
        return None

    referral = Referral.objects.filter(
        referrer=referred_user.referred_by,
        referred_user=referred_user,
        is_active=True,
    ).first()
    if not referral:
        return None

    reward_amount = Decimal(getattr(settings, "REFERRAL_REWARD_AMOUNT", 10.00))
    if reward_amount <= 0:
        return None

    try:
        wallet, _ = Wallet.objects.get_or_create(user=referred_user.referred_by)
        wallet.add_balance(
            amount=reward_amount,
            transaction_type=Transaction.TransactionType.REFERRAL_REWARD,
            reference=f"referral-{referred_user.id}-{referral.id}",
        )

        referral.reward_amount = reward_amount
        referral.is_active = False
        referral.save(update_fields=["reward_amount", "is_active"])

        try:
            Notification.objects.create(
                user=referred_user.referred_by,
                title="Referral reward earned",
                message=(
                    f"You earned ${reward_amount:.2f} because {referred_user.email} completed their first deposit."
                ),
            )
        except Exception:
            pass

        return referral
    except Exception:
        return None


@receiver(post_save, sender=User)
def update_last_active_for_login(sender, instance, **kwargs):
    if instance.last_active is None:
        instance.last_active = timezone.now()
        instance.save(update_fields=["last_active"])
