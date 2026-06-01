"""
Script to initialize plans in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from core.models import Plan

# Create default plans
plans_data = [
    {
        'plan_level': 1,
        'title': 'Plan 1',
        'amount': 20.00,
        'reward_multiplier': 1.0,
        'daily_earning_limit': 50.00,
        'max_tasks_per_day': 20,
        'duration_days': 30,
        'active': True,
    },
    {
        'plan_level': 2,
        'title': 'Plan 2',
        'amount': 50.00,
        'reward_multiplier': 1.5,
        'daily_earning_limit': 100.00,
        'max_tasks_per_day': 40,
        'duration_days': 30,
        'active': True,
    },
    {
        'plan_level': 3,
        'title': 'Plan 3',
        'amount': 80.00,
        'reward_multiplier': 2.0,
        'daily_earning_limit': 200.00,
        'max_tasks_per_day': 60,
        'duration_days': 30,
        'active': True,
    },
    {
        'plan_level': 4,
        'title': 'Plan 4',
        'amount': 120.00,
        'reward_multiplier': 2.5,
        'daily_earning_limit': 350.00,
        'max_tasks_per_day': 100,
        'duration_days': 30,
        'active': True,
    },
]

for plan_data in plans_data:
    plan, created = Plan.objects.update_or_create(
        plan_level=plan_data['plan_level'],
        defaults=plan_data
    )
    status = 'Created' if created else 'Updated'
    print(f'{status}: {plan.title} - ${plan.amount}')

print(f'\nTotal plans: {Plan.objects.count()}')
