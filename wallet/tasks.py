from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from datetime import timedelta
from accounts.models import User
from notifications.models import Notification
from .models import Transaction, Wallet

@shared_task
def reward_active_users():
    from core.models import UserPlan
    cutoff = timezone.now() - timedelta(minutes=15)
    # Users active in last 15 mins who haven't been rewarded in the last hour
    users = User.objects.filter(last_active__gte=cutoff, is_active=True).exclude(
        last_rewarded_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    for user in users:
        # Base reward
        base_reward = 0.50
        reward_amount = base_reward
        
        # Check active plans
        active_plan = UserPlan.objects.filter(user=user).select_related('plan').first()
        if active_plan:
            # Check if plan is still valid (duration check)
            expiry_date = active_plan.joined_at + timedelta(days=active_plan.plan.duration_days)
            if timezone.now() <= expiry_date:
                reward_amount = float(base_reward) * float(active_plan.plan.reward_multiplier or 1.0)
            else:
                # Plan expired, maybe deactivate it? 
                # For now just fall back to base reward
                pass

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet.add_balance(
                amount=reward_amount,
                transaction_type=Transaction.TransactionType.ACTIVITY_REWARD,
                reference=f"auto-profit-{user.id}-{timezone.now().strftime('%Y%m%d%H')}"
            )
            
            user.last_rewarded_at = timezone.now()
            user.save(update_fields=["last_rewarded_at"])
            
            Notification.objects.create(
                user=user,
                title="Investment Profit Granted",
                message=f"You earned ${reward_amount} in passive profit from your active plan!",
            )

