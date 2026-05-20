from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils.functional import cached_property
from django.db import transaction as db_transaction

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet({self.user.email})"

    @cached_property
    def display_balance(self):
        return float(self.balance)

    def add_balance(self, amount, transaction_type, reference=None, description=None):
        """Safely add balance to wallet and create transaction record"""
        with db_transaction.atomic():
            self.balance = F("balance") + amount
            self.save(update_fields=["balance"])
            self.refresh_from_db()
            Transaction.objects.create(
                user=self.user,
                wallet=self,
                amount=amount,
                transaction_type=transaction_type,
                reference=reference or "",
            )

    def subtract_balance(self, amount, transaction_type, reference=None, description=None):
        """Safely subtract balance from wallet and create transaction record"""
        with db_transaction.atomic():
            self.balance = F("balance") - amount
            self.save(update_fields=["balance"])
            self.refresh_from_db()
            Transaction.objects.create(
                user=self.user,
                wallet=self,
                amount=-amount,
                transaction_type=transaction_type,
                reference=reference or "",
            )

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        TASK_REWARD = "TASK_REWARD", "Task Reward"
        ACTIVITY_REWARD = "ACTIVITY_REWARD", "Activity Reward"
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.transaction_type} {self.amount}"

class Withdrawal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    wallet_address = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-requested_at",)

    def __str__(self):
        return f"Withdrawal {self.amount} - {self.status}"

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)  # USDT, BTC, ETH
    network = models.CharField(max_length=50)  # TRC20, ERC20, BTC
    wallet_address = models.CharField(max_length=255)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.network})"

class CryptoDeposit(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_deposits")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_hash = models.CharField(max_length=255, unique=True)
    proof_image = models.ImageField(upload_to="deposit_proofs/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Crypto {self.amount} {self.payment_method.name} - {self.status}"
