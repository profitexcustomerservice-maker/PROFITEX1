import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.contrib.auth import get_user_model
from wallet.models import Withdrawal, Wallet

User = get_user_model()
print("Total Withdrawals in DB:", Withdrawal.objects.count())
print("All Withdrawals:", list(Withdrawal.objects.all().values('id', 'user_id', 'amount', 'status')))

# Check if there are multiple Withdrawal models?
# Only wallet.models.Withdrawal should exist.

# Let's see if admin_panel filters them out
print("Withdrawals with PENDING status:", Withdrawal.objects.filter(status=Withdrawal.Status.PENDING).count())

user = User.objects.first()
if user:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    print("Test User:", user.id, "Wallet Balance:", wallet.balance)
    
    # Check what kind of withdrawals exist
    qs = Withdrawal.objects.select_related('user').order_by('-requested_at')
    print("Queryset fetched by admin view:", len(qs))
else:
    print("No users found.")
