#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from core.models import Task, Plan
from accounts.models import User
from wallet.models import Wallet

# Create test tasks
task1 = Task.objects.create(title='Watch Product Video', description='Watch our promotional video and earn rewards', reward=5.00, media_type='video')
task2 = Task.objects.create(title='Share on Social Media', description='Share our product on your social media', reward=3.00)
task3 = Task.objects.create(title='Complete Survey', description='Fill out our customer satisfaction survey', reward=2.50)

# Create test plans
plan1 = Plan.objects.create(title='Basic Plan', description='Get started with basic earning opportunities', amount=10.00, reward=15.00, duration_days=7)
plan2 = Plan.objects.create(title='Premium Plan', description='Maximum earning potential with premium features', amount=25.00, reward=40.00, duration_days=14)

# Create test user
test_user = User.objects.create_user(email='user@test.com', password='test123', first_name='Test', last_name='User')

print('Test data created successfully!')
print(f'Tasks: {Task.objects.count()}')
print(f'Plans: {Plan.objects.count()}')
print(f'Users: {User.objects.count()}')
print(f'Wallets: {Wallet.objects.count()}')
