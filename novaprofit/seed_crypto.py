import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from wallet.models import PaymentMethod

methods = [
    {
        "name": "USDT",
        "network": "TRC20",
        "wallet_address": "TQpA4vYF8S6XqYqYqYqYqYqYqYqYqYqYqY", # Placeholder
    },
    {
        "name": "Bitcoin",
        "network": "BTC",
        "wallet_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", # Placeholder
    },
    {
        "name": "Ethereum",
        "network": "ERC20",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", # Placeholder
    }
]

for m in methods:
    obj, created = PaymentMethod.objects.get_or_create(
        name=m["name"],
        network=m["network"],
        defaults={"wallet_address": m["wallet_address"]}
    )
    if created:
        print(f"Created {m['name']} ({m['network']})")
    else:
        print(f"{m['name']} already exists")
