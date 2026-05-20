import os
import django
import json
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.contrib.auth import get_user_model
from wallet.models import Withdrawal, Wallet

User = get_user_model()
user, created = User.objects.get_or_create(email="test@example.com", defaults={"password": "test"})
wallet, _ = Wallet.objects.get_or_create(user=user)
wallet.balance = 200.00
wallet.save()

client = Client()
client.force_login(user)

response = client.post('/api/withdrawals/', {'amount': 100, 'wallet_address': 'test-wallet-address'})
print("POST Response Status:", response.status_code)
print("POST Response Data:", response.content.decode('utf-8'))

print("Withdrawals after POST:", Withdrawal.objects.filter(user=user).count())
