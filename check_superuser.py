#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from accounts.models import User

try:
    user = User.objects.get(email='josuekabalisa@gmail.com')
    print(f'User found: {user.email}')
    print(f'is_active: {user.is_active}')
    print(f'is_admin: {user.is_admin}')
    print(f'is_superuser: {user.is_superuser}')
    print(f'is_staff: {user.is_staff}')
    print(f'Password matches: {user.check_password("Uwamahor12345@@")}')
except User.DoesNotExist:
    print('User not found')
except Exception as e:
    print(f'Error: {e}')
