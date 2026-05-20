from rest_framework import serializers
from .models import Transaction, Withdrawal, PaymentMethod, CryptoDeposit

class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Transaction
        fields = ("id", "user", "user_email", "amount", "transaction_type", "reference", "created_at")

class WithdrawalSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Withdrawal
        fields = ("id", "user", "user_email", "amount", "wallet_address", "status", "requested_at", "processed_at", "reference")
        read_only_fields = ("status", "requested_at", "processed_at", "reference", "user")

    def validate_wallet_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Wallet address is required.")
        return value.strip()

    def validate_amount(self, value):
        # Only validate when request context is available (DRF viewset usage)
        request = self.context.get("request")
        if request is None:
            return value

        user = request.user
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be positive.")
        if not hasattr(user, 'wallet'):
            raise serializers.ValidationError("No wallet found.")
        if user.wallet.balance < value:
            raise serializers.ValidationError("Insufficient balance.")
        return value

    def create(self, validated_data):
        validated_data["reference"] = f"WDL-{validated_data['user'].id}-{validated_data['amount']}"
        return super().create(validated_data)

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"

class CryptoDepositSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.ReadOnlyField(source="payment_method.name")
    payment_method_network = serializers.ReadOnlyField(source="payment_method.network")
    username = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = CryptoDeposit
        fields = "__all__"
        read_only_fields = ("user", "status", "created_at", "processed_at")
