"""
Management command to assign a plan to a user
Usage: python manage.py assign_user_plan <email> <plan_level> [days]

Example:
    python manage.py assign_user_plan test@example.com 1 30
    python manage.py assign_user_plan admin@example.com 4 90
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from core.models import Plan, UserPlan


class Command(BaseCommand):
    help = 'Assign a plan subscription to a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('plan_level', type=int, choices=[1, 2, 3, 4], help='Plan level (1-4)')
        parser.add_argument('days', type=int, nargs='?', default=30, help='Days until expiration (default: 30)')

    def handle(self, *args, **options):
        email = options['email']
        plan_level = options['plan_level']
        days = options['days']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{email}" does not exist')

        try:
            plan = Plan.objects.get(plan_level=plan_level)
        except Plan.DoesNotExist:
            raise CommandError(f'Plan with level {plan_level} does not exist')

        # Create or update user plan
        expires_at = timezone.now() + timedelta(days=days)
        user_plan, created = UserPlan.objects.update_or_create(
            user=user,
            plan=plan,
            defaults={
                'is_active': True,
                'expires_at': expires_at,
            }
        )

        # Update user's current plan level
        user.current_plan_level = plan_level
        user.save(update_fields=['current_plan_level'])

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} plan subscription for {user.email}:\n'
                f'  Plan: {plan.title} (Level {plan.plan_level})\n'
                f'  Amount: ${plan.amount}\n'
                f'  Reward Multiplier: {plan.reward_multiplier}x\n'
                f'  Daily Limit: ${plan.daily_earning_limit}\n'
                f'  Max Tasks/Day: {plan.max_tasks_per_day}\n'
                f'  Expires: {expires_at.strftime("%Y-%m-%d %H:%M:%S")} (in {days} days)\n'
                f'  Active: True'
            )
        )
