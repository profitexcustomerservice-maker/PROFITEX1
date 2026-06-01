"""
Utility functions for plan validation and checking
"""
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import UserPlan


def user_has_active_plan(user):
    """
    Check if user has an active, non-expired plan.
    Returns: bool
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.plans.filter(is_active=True).exclude(
        expires_at__isnull=False,
        expires_at__lt=timezone.now()
    ).exists()


def get_user_active_plan(user):
    """
    Get user's active plan subscription (if any).
    Returns: UserPlan or None
    """
    if not user or not user.is_authenticated:
        return None
    
    active_plans = user.plans.filter(is_active=True).exclude(
        expires_at__isnull=False,
        expires_at__lt=timezone.now()
    ).select_related('plan')
    
    return active_plans.first()


def get_user_highest_plan_level(user):
    """
    Get user's highest active plan level (0 if none).
    Returns: int (0-4)
    """
    active_plan = get_user_active_plan(user)
    return active_plan.plan.plan_level if active_plan else 0


def check_user_has_active_plan(user):
    """
    Verify user has active plan, raise PermissionDenied if not.
    Raises: PermissionDenied with descriptive message
    """
    if not user_has_active_plan(user):
        raise PermissionDenied(
            detail="You must purchase a plan to access this feature. Please buy a plan to continue."
        )


def get_plan_info(user):
    """
    Get comprehensive plan information for a user.
    Returns: dict with plan details or empty dict if no plan
    """
    active_plan = get_user_active_plan(user)
    
    if not active_plan:
        return {
            "has_plan": False,
            "plan_level": 0,
            "plan_name": None,
            "days_remaining": None,
            "expires_at": None,
        }
    
    plan = active_plan.plan
    days_remaining = active_plan.days_remaining()
    
    return {
        "has_plan": True,
        "plan_level": plan.plan_level,
        "plan_name": plan.title,
        "plan_amount": str(plan.amount),
        "reward_multiplier": str(plan.reward_multiplier),
        "daily_limit": str(plan.daily_earning_limit),
        "max_tasks_per_day": plan.max_tasks_per_day,
        "days_remaining": days_remaining,
        "expires_at": active_plan.expires_at.isoformat() if active_plan.expires_at else None,
        "joined_at": active_plan.joined_at.isoformat(),
    }
