from django.contrib import admin
from .models import Transaction, Withdrawal, Wallet, PaymentMethod, CryptoDeposit

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__email",)
    list_select_related = ("user",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "reference", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__email", "reference")
    list_select_related = ("user", "wallet")

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "requested_at", "processed_at")
    list_filter = ("status",)
    search_fields = ("user__email",)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "network", "wallet_address", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "name")
    search_fields = ("name", "wallet_address")

@admin.register(CryptoDeposit)
class CryptoDepositAdmin(admin.ModelAdmin):
    list_display = ("user", "payment_method", "amount", "status", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("user__email", "transaction_hash")
    readonly_fields = ("created_at", "processed_at")
